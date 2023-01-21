from odoo import models, fields, api, tools, _
from odoo.tools.misc import format_datetime, formatLang, get_lang, format_amount
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

class PickingVendorNameINT(models.Model):
    _inherit = 'stock.picking'
    partner_name = fields.Char(readonly=True, string='Vendor Name', compute='compute_partner')
    
    def compute_partner(self):
        for rec in self:
            po = self.env['purchase.order'].search([('name', '=', rec.origin)])
            if po:
                partner = self.env['res.partner'].search([('id', '=', po.partner_id.id)])
                if partner:
                    rec.partner_name = partner.name
                else:
                    rec.partner_name = ''
            else:
                rec.partner_name = ''
            
    def createupdate_qc(self,id,name,company,state):
        if "/INT/" in name and state=="assigned":
            transferdata = self.env['stock.move.line'].search([('picking_id', '=', id)]).sorted(key = 'id')
            if transferdata:
                qcdata = self.env['quality.check'].search([('picking_id', '=', id)]).sorted(key = 'id')
                for tr in transferdata:
                    qcproduct = qcdata.search([('product_id', '=', tr.product_id.id),('lot_id', '=', False)])
                    qclotexist = self.env['quality.check'].search([('lot_id', '=', tr.lot_id.id)])
                    if qcproduct:
                        qcproduct.write({'lot_id': tr.lot_id.id})
                    elif qclotexist:
                        qty=1
                    else:
                        qcpoint = self.env['quality.point'].search([('company_id', '=', company.id)]).sorted(key = 'id')[:1]
                        qcdata.create({'point_id': qcpoint.id,
                                       'quality_state': 'none',
                                       'product_id': tr.product_id.id,
                                       'picking_id': id,
                                       'lot_id': tr.lot_id.id,
                                       'team_id': 1,
                                       'company_id': company.id,
                                       'test_type_id': 3})
                        
                     
                    
                    
class ProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    rejected = fields.Boolean(store=True, string='Rejected', readonly=False, tracking=True)
    unit_price = fields.Float(readonly=False, store=True, string='Unit Price', digits='Product Unit of Measure')
    pur_price = fields.Float(readonly=False, store=True, string='Purchase Price', digits='Product Unit of Measure')
    landed_cost = fields.Float(readonly=False, store=True, string='Landed Cost', digits='Product Unit of Measure')
    
    # @api.depends('pur_price')
    # def _compute_pur_price(self):
    #     for rec in self:
    #         if rec.purchase_order_ids:
    #             rec.pur_price = self.env['purchase.order.line'].search([('order_id', 'in', (rec.purchase_order_ids)),('product_id', '==', rec.product_id.id)]).avg(price_unit)

    # @api.model
    # def create(self, vals):
    #     raise UserError((vals.get('id'),vals.get('name'),vals.get('purchase_order_ids')))
        # stock_moves = self.env['stock.move.line'].search([('lot_id', '=', vals.get('id')),('state', '=', 'done') ]).mapped('move_id')
        # stock_moves = self.env['stock.move.line'].search([('state', '=', 'done')]).mapped('move_id')
        # stock_moves = stock_moves.search([('id', 'in', stock_moves.ids)]).filtered(lambda move: move.picking_id.location_id.usage == 'supplier' and move.state == 'done')
        # purchase_order_ids = stock_moves.mapped('purchase_line_id.order_id')
        # price = self.env['purchase.order.line'].search([('id','in',(purchase_order_ids))])
        # pr = avg(price.mapped('price_unit'))
        # if purchase_order_ids:
        #     vals['pur_price'] = pr
        # return super(ProductionLot, self).create(vals)
    
    
    # @api.model_create_multi
    # def create(self, vals_list):
    #     self._check_create()
    #     for values in vals_list:
    #         stock_moves = self.env['stock.move.line'].search([
    #             ('lot_name', '=', values.get('name')),
    #             ('product_id', '=', values.get('product_id'))
    #         ])
    #         po_line = self.env['purchase.order.line'].search([
    #             ('order_id.name', '=', stock_moves.picking_id.origin),
    #             ('product_id', '=', values.get('product_id'))
    #         ],limit=1)
    #         price = 0.0
    #         if po_line:
    #             currency = po_line.currency_id.id
    #             price = format_amount(self.env, round(po_line.price_unit, 4), currency)
    #         else:
    #             po_line = self.env['purchase.order.line'].search([('product_id', '=', values.get('product_id'))]).sorted(key = 'id', reverse=True)[:1]
    #             currency = po_line.currency_id.id
    #             price = format_amount(self.env, round(po_line.price_unit, 4), currency)
    #         values.update(pur_price=price,unit_price=price)
    #     return super(ProductionLot, self.with_context(mail_create_nosubscribe=True)).create(vals_list)

class IncludeCateTypeInPT(models.Model):
    _inherit = 'stock.move.line'
    parent_categ_type = fields.Char(related='product_id.categ_type.parent_id.name', related_sudo=False, readonly=True, store=True, string='Parent Category')
    category_type = fields.Char(related='product_id.categ_type.name', related_sudo=False, readonly=True, store=True, string='Category Type')
    qty_onhand = fields.Float(related='lot_id.product_qty', readonly=True, store=True, string='Quantity')
    unit_price = fields.Float(related='product_id.standard_price', readonly=True, store=True, string='Price', digits='Unit Price')
    value = fields.Float(compute='_compute_product_value', readonly=True, store=True, string='Value')
    duration = fields.Integer(string='Duration', compute='_compute_duration', store=True, readonly=True)
    pur_price = fields.Float(compute='_compute_purchase_price', readonly=True, string='Unit Price', digits='Unit Price')
    unit_price = fields.Float(related='lot_id.unit_price', readonly=False, store=True, string='Lot Price', digits='Unit Price')
    
    #pur_value = fields.Float(compute='_compute_purchase_value', readonly=True, string='Purchase Value')
    #product_id.categ_type.parent_id.name 
    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_product_value(self):
        for record in self:
            price = record.pur_price
            if record.unit_price:
                if record.unit_price>0:
                    price = record.unit_price
            record['value'] = round(record.qty_onhand * price,2)
            
    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom: {product, name, description, qty_done, product_uom}, ...}
        """
        aggregated_move_lines = {}
        for move_line in self:
            name = move_line.product_id.display_name
            description = move_line.move_id.description_picking
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = str(move_line.product_id.id) + "_" + name + (description or "") + "uom " + str(uom.id)

            if line_key not in aggregated_move_lines:
                aggregated_move_lines[line_key] = {'name': name,
                                                   'description': description,
                                                   'qty_done': move_line.qty_done,
                                                   'qty_onhand': move_line.qty_onhand,
                                                   'value': move_line.value,
                                                   'product_uom': uom.name,
                                                   'product': move_line.product_id}
            else:
                aggregated_move_lines[line_key]['qty_done'] += move_line.qty_done
                aggregated_move_lines[line_key]['qty_onhand'] += move_line.qty_onhand
                aggregated_move_lines[line_key]['value'] += move_line.value
        return aggregated_move_lines
    
    @api.depends('product_id')
    def _compute_duration(self):
        for line in self:
            sc_date = line.create_date
            if line.x_studio_schedule_date:
                sc_date = line.x_studio_schedule_date
            x = datetime.now().replace(hour=0, minute =0, second = 0, microsecond = 0)
            y = sc_date.replace(hour=23, minute =59, second = 59, microsecond = 0)
            dur = x-y
            line.duration = dur.days+1
            
    def _update_duration(self):
        move_line = self.env['stock.move.line'].search([('id', '>', 0)])
        for record in move_line:
            sc_date = record.create_date
            if record.x_studio_schedule_date:
                sc_date = record.x_studio_schedule_date
            x = datetime.now().replace(hour=0, minute =0, second = 0, microsecond = 0)
            y = sc_date.replace(hour=23, minute =59, second = 59, microsecond = 0)
            dur = x-y
            record[-1].write({'duration' : dur.days+1})
            
    def _compute_purchase_price(self):
        for record in self:
            if record.lot_id.unit_price:
                record.pur_price = record.lot_id.unit_price
            else:
                stock_v_layer = self.env['stock.valuation.layer'].search([('stock_move_id', '=', int(record.move_id)),('product_id', '=', int(record.product_id)),('description', 'like', '/IN/')])
                if stock_v_layer:
                    record.pur_price = round(stock_v_layer.unit_cost,4)
                else:
                    record.pur_price = record.unit_price
                
    #def _compute_purchase_value(self):
    #    for record in self:
    #        record['pur_value'] = round(record.qty_done * record.pur_price,2)