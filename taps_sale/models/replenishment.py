import logging
from collections import defaultdict
from datetime import datetime, time
from dateutil import relativedelta
from itertools import groupby
from json import dumps
from psycopg2 import OperationalError

from odoo import SUPERUSER_ID, _, api, fields, models, registry
from odoo.addons.stock.models.stock_rule import ProcurementException
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression
from odoo.tools import add, float_compare, frozendict, split_every, format_date

_logger = logging.getLogger(__name__)


class Orderpoint(models.Model):
    _inherit = "stock.warehouse.orderpoint"
    
    qty_to_order = fields.Float('To Order', digits='Product Unit of Measure', compute='_compute_qty_to_order', store=True, readonly=False)
    #sale_line_id = fields.Many2one('sale.order.line', string='Sale Order Line', store=True)
    
    @api.depends('qty_multiple', 'qty_forecast', 'product_min_qty', 'product_max_qty')
    def _compute_qty_to_order(self):
        for orderpoint in self:
            if not orderpoint.product_id or not orderpoint.location_id:
                orderpoint.qty_to_order = False
                continue
            qty_to_order = 0.0
            rounding = orderpoint.product_uom.rounding
            if float_compare(orderpoint.qty_forecast, orderpoint.product_min_qty, precision_rounding=rounding) < 0:
                qty_to_order = max(orderpoint.product_min_qty, orderpoint.product_max_qty) - orderpoint.qty_forecast

                remainder = orderpoint.qty_multiple > 0 and qty_to_order % orderpoint.qty_multiple or 0.0
                if float_compare(remainder, 0.0, precision_rounding=rounding) > 0:
                    qty_to_order += orderpoint.qty_multiple #- remainder
            orderpoint.qty_to_order = qty_to_order    
    
    
    def _get_orderpoint_action_test(self):
        """Create manual orderpoints for missing product in each warehouses. It also removes
        orderpoints that have been replenish. In order to do it:
        - It uses the report.stock.quantity to find missing quantity per product/warehouse
        - It checks if orderpoint already exist to refill this location.
        - It checks if it exists other sources (e.g RFQ) tha refill the warehouse.
        - It creates the orderpoints for missing quantity that were not refill by an upper option.

        return replenish report ir.actions.act_window
        """
        action = self.env["ir.actions.actions"]._for_xml_id("stock.action_orderpoint_replenish")
        action['context'] = self.env.context
        # Search also with archived ones to avoid to trigger product_location_check SQL constraints later
        # It means that when there will be a archived orderpoint on a location + product, the replenishment
        # report won't take in account this location + product and it won't create any manual orderpoint
        # In master: the active field should be remove
        orderpoints = self.env['stock.warehouse.orderpoint'].with_context(active_test=False).search([])
        # Remove previous automatically created orderpoint that has been refilled.
        to_remove = orderpoints.filtered(lambda o: o.create_uid.id == SUPERUSER_ID and o.qty_to_order <= 0.0 and o.trigger == 'manual')
        to_remove.unlink()
        orderpoints = orderpoints - to_remove
        to_refill = defaultdict(float)
        all_product_ids = []
        all_warehouse_ids = []
        all_sale_line_ids = []
        # Take 3 months since it's the max for the forecast report
        to_date = add(fields.date.today(), months=3)
        qty_by_product_warehouse = self.env['report.stock.quantity'].read_group(
            [('date', '=', to_date), ('state', '=', 'forecast')],
            ['product_id', 'product_qty', 'warehouse_id', 'sale_line_id'],
            ['product_id', 'warehouse_id', 'sale_line_id'], lazy=False)
        for group in qty_by_product_warehouse:
            warehouse_id = group.get('warehouse_id') and group['warehouse_id'][0]
            sale_line_id = group.get('sale_line_id') and group['sale_line_id'][0]
            if group['product_qty'] >= 0.0 or not warehouse_id  or not sale_line_id:
                continue
            all_product_ids.append(group['product_id'][0])
            all_warehouse_ids.append(warehouse_id)
            all_sale_line_ids.append(sale_line_id)
            to_refill[(group['product_id'][0], warehouse_id, sale_line_id)] = group['product_qty']
        if not to_refill:
            return action
        
        # Recompute the forecasted quantity for missing product today but at this time
        # with their real lead days.
        key_to_remove = []

        # group product by lead_days and warehouse in order to read virtual_available
        # in batch
        pwh_per_day = defaultdict(list)
        for (product, warehouse, saleorder), quantity in to_refill.items():
            product = self.env['product.product'].browse(product).with_prefetch(all_product_ids)
            warehouse = self.env['stock.warehouse'].browse(warehouse).with_prefetch(all_warehouse_ids)
            saleorder = self.env['sale.order.line'].browse(saleorder).with_prefetch(all_sale_line_ids)
            rules = product._get_rules_from_location(warehouse.lot_stock_id)
            lead_days = rules.with_context(bypass_delay_description=True)._get_lead_days(product)[0]
            pwh_per_day[(lead_days, warehouse)].append(product.id)
        for (days, warehouse), p_ids in pwh_per_day.items():
            products = self.env['product.product'].browse(p_ids)
            qties = products.with_context(
                warehouse=warehouse.id,
                to_date=fields.datetime.now() + relativedelta.relativedelta(days=days)
            ).read(['virtual_available'])
            for qty in qties:
                if float_compare(qty['virtual_available'], 0, precision_rounding=product.uom_id.rounding) >= 0:
                    key_to_remove.append((qty['id'], warehouse.id, saleorder.id))
                else:
                    to_refill[(qty['id'], warehouse.id, saleorder.id)] = qty['virtual_available']

        for key in key_to_remove:
            del to_refill[key]
        if not to_refill:
            return action

        # Remove incoming quantity from other origin than moves (e.g RFQ)
        product_ids, warehouse_ids, sale_line_ids = zip(*to_refill)
        dummy, qty_by_product_wh = self.env['product.product'].browse(product_ids)._get_quantity_in_progress(warehouse_ids=warehouse_ids)
        rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        # Group orderpoint by product-warehouse
        orderpoint_by_product_warehouse = self.env['stock.warehouse.orderpoint'].read_group(
            [('id', 'in', orderpoints.ids)],
            ['product_id', 'warehouse_id', 'sale_line_id', 'qty_to_order:sum'],
            ['product_id', 'warehouse_id', 'sale_line_id'], lazy=False)
        orderpoint_by_product_warehouse = {
            (record.get('product_id')[0], record.get('warehouse_id')[0], record.get('sale_line_id')[0]): record.get('qty_to_order')
            for record in orderpoint_by_product_warehouse
        }
        for (product, warehouse, saleorder), product_qty in to_refill.items():
            qty_in_progress = qty_by_product_wh.get((product, warehouse, saleorder)) or 0.0
            qty_in_progress += orderpoint_by_product_warehouse.get((product, warehouse, saleorder), 0.0)
            # Add qty to order for other orderpoint under this warehouse.
            if not qty_in_progress:
                continue
            to_refill[(product, warehouse, saleorder)] = product_qty + qty_in_progress
        to_refill = {k: v for k, v in to_refill.items() if float_compare(
            v, 0.0, precision_digits=rounding) < 0.0}

        lot_stock_id_by_warehouse = self.env['stock.warehouse'].with_context(active_test=False).search_read([
            ('id', 'in', [g[1] for g in to_refill.keys()])
        ], ['lot_stock_id'])
        lot_stock_id_by_warehouse = {w['id']: w['lot_stock_id'][0] for w in lot_stock_id_by_warehouse}

        saleorder_line = self.env['sale.order.line'].search_read([
            ('id', 'in', [g[2] for g in to_refill.keys()])
        ], ['id'])
        saleorder_line = {w['id']: w['id'][0] for w in saleorder_line}
        
        
        # With archived ones to avoid `product_location_check` SQL constraints
        orderpoint_by_product_location = self.env['stock.warehouse.orderpoint'].with_context(active_test=False).read_group(
            [('id', 'in', orderpoints.ids)],
            ['product_id', 'location_id', 'sale_line_id', 'ids:array_agg(id)'],
            ['product_id', 'location_id', 'sale_line_id'], lazy=False)
        orderpoint_by_product_location = {
            (record.get('product_id')[0], record.get('location_id')[0], record.get('sale_line_id')[0]): record.get('ids')[0]
            for record in orderpoint_by_product_location
        }

        orderpoint_values_list = []
        for (product, warehouse, saleorder), product_qty in to_refill.items():
            lot_stock_id = lot_stock_id_by_warehouse[warehouse]
            sale_lineid = saleorder_line[saleorder]
            orderpoint_id = orderpoint_by_product_location.get((product, lot_stock_id, sale_lineid))
            if orderpoint_id:
                self.env['stock.warehouse.orderpoint'].browse(orderpoint_id).qty_forecast += product_qty
            else:
                orderpoint_values = self.env['stock.warehouse.orderpoint']._get_orderpoint_values(product, lot_stock_id, sale_lineid)
                orderpoint_values.update({
                    'name': _('Replenishment Report'),
                    'warehouse_id': warehouse,
                    'sale_line_id': saleorder,
                    'company_id': self.env['stock.warehouse'].browse(warehouse).company_id.id,
                })
                orderpoint_values_list.append(orderpoint_values)

        orderpoints = self.env['stock.warehouse.orderpoint'].with_user(SUPERUSER_ID).create(orderpoint_values_list)
        for orderpoint in orderpoints:
            orderpoint_wh = orderpoint.location_id.get_warehouse()
            orderpoint.route_id = next((r for r in orderpoint.product_id.route_ids if not r.supplied_wh_id or r.supplied_wh_id == orderpoint_wh), orderpoint.route_id)
            if not orderpoint.route_id:
                orderpoint._set_default_route_id()
        return action

#     @api.model
#     def _get_orderpoint_values(self, product, location, saleorder):
#         return {
#             'product_id': product,
#             'location_id': location,
#             'sale_line_id': saleorder,
#             'product_max_qty': 0.0,
#             'product_min_qty': 0.0,
#             'trigger': 'manual',
#         }
    
    
    #qty_to_order = fields.Float('To Order', store=True, readonly=False)
    #sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True)
    #sale_order_id = fields.Many2one(string='Sales Order', related='sale_order_line.order_id', store=True, readonly=True)
    
    
#     def action_replenish(self):
#         now = datetime.now()
#         self._procure_orderpoint_confirm(company_id=self.env.company)
# #         self.replenish_subproducts()
#         notification = False
#         if len(self) == 1:
#             notification = self.with_context(written_after=now)._get_replenishment_order_notification()
#         # Forced to call compute quantity because we don't have a link.
#         self._compute_qty()
#         self.filtered(lambda o: o.create_uid.id == SUPERUSER_ID and o.qty_to_order <= 0.0 and o.trigger == 'manual').unlink()
#         return notification
    
#     def replenish_subproducts(self):
#         #if not self.product_id.default_code:
#         if not self.product_id.default_code:
#             inner_bom = self.env['mrp.bom.line'].search([('bom_id', '=', self.sale_order_line.bom_id)])
#             for bomline in inner_bom:
#                 order_point = {}
#                 order_point = {
#                     'name':'Replenishment Report',
#                     'trigger':'manual',
#                     'active':True,
#                     'warehouse_id':1,
#                     'location_id':8,
#                     'product_id':bomline.product_id.id,
#                     'product_category_id':bomline.product_id.categ_id.id,
#                     'product_min_qty':0,
#                     'product_max_qty':0,
#                     'qty_multiple':1,
#                     #'group_id':0.0,
#                     'company_id':self.company_id.id,
#                     'route_id':1,
#                     'qty_to_order':self.qty_to_order * bomline.product_qty,
#                     'bom_id':bomline.bom_id.id,
#                     #'supplier_id':0.0,
#                     'sale_order_line':self.sale_order_line.id,
#                     'sale_order_id':self.sale_order_id.id
#                 }
#                 self.env['stock.warehouse.orderpoint'].create(order_point)