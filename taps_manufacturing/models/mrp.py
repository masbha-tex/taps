import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

SIZE_BACK_ORDER_NUMERING = 3


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', store=True, readonly=True)
    qc_pass_qty = fields.Float(string='QC Pass Quantity', default=0.0, store=True)
    
    shade = fields.Text(string='Shade', store=True)
    finish = fields.Text(string='Finish', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    
    # def action_split(self):
    #     self.ensure_one()
    #     return {
    #         'name': _('Split'),
    #         'view_mode': 'form',
    #         'res_model': 'mrp.split',
    #         'view_id': self.env.ref('mrp.action_split_mrp').id,
    #         'type': 'ir.actions.act_window',
    #         'res_id': self.id,
    #         'context': {'default_mo_id': self.id,'default_company_id': self.company_id.id, 'show_mo_qty':self.product_qty},
    #         'target': 'new',
    #     }
    
    def action_split(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action    
    
    def mrp_values(self,id,origin,product,qty,uom,bom,start_date,end_date,shade,finish,sizein,sizecm):
        if sizein == 'N/A':
            sizein = ''
        if sizecm == 'N/A':
            sizecm = ''
        values = {
            'priority': 0,
            'origin': origin,
            'product_id': product,
            'product_qty': qty,
            'product_uom_id': uom,
            #'qty_producing': 0,
            'product_uom_qty': qty,
            'picking_type_id': 8,
            'location_src_id': 8,
            'location_dest_id': 8,
            'date_planned_start': start_date,
            'date_planned_finished': end_date,
            'date_deadline': end_date,
            'bom_id': bom,
            'state': 'draft',
            #'user_id': self.company_id.id,
            'company_id': self.company_id.id,
            #'procurement_group_id': self.company_id.id,
            'propagate_cancel': False,
            'is_locked': False,
            'production_location_id': 15,
            'consumption': 'warning',
            'oa_id':self.oa_id.id,
            'sale_order_line':id,
            'shade':shade,
            'finish':finish,
            'sizein':sizein,
            'sizecm':sizecm
        }
        return values
    

    def split_mo(self,mo,split_line):
        production = self.env["mrp.production"].browse(mo)
        spl_qty = sum(split_line.mapped('product_qty'))
        mrp_qty = production.product_qty
        bal_qty = mrp_qty - spl_qty
        if bal_qty>0:
            production.update({'product_qty':bal_qty})
        row = 0
        for line in split_line:
            if (bal_qty == 0) and (row == 0):
                production.update({'product_qty':line.product_qty})
            else:
                mrp_production = self.env['mrp.production'].create(self.mrp_values(None,production.name,production.product_id.id,line.product_qty,production.product_uom_id.id,production.bom_id.id,line.date_planned_start,line.date_planned_finished))
                mrp_production.move_raw_ids.create(mrp_production._get_moves_raw_values())
                mrp_production._onchange_workorder_ids()
                mrp_production._create_update_move_finished()
            row += 1
    
    def _create_workorder(self):
        for production in self:
            if not production.bom_id:
                continue
            workorders_values = []

            product_qty = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
            exploded_boms, dummy = production.bom_id.explode(production.product_id, product_qty / production.bom_id.product_qty, picking_type=production.bom_id.picking_type_id)

            for bom, bom_data in exploded_boms:
                # If the operations of the parent BoM and phantom BoM are the same, don't recreate work orders.
                if not (bom.operation_ids and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.operation_ids != bom.operation_ids)):
                    continue
                for operation in bom.operation_ids:
                    workorders_values += [{
                        'name': operation.name,
                        'production_id': production.id,
                        'workcenter_id': operation.workcenter_id.id,
                        'product_uom_id': production.product_uom_id.id,
                        'operation_id': operation.id,
                        'state': 'pending',
                        'consumption': production.consumption,
                        'oa_id': production.oa_id.id,
                        'sale_order_line': production.sale_order_line.id,
                    }]
            production.workorder_ids = [(5, 0)] + [(0, 0, value) for value in workorders_values]
            for workorder in production.workorder_ids:
                workorder.duration_expected = workorder._get_duration_expected()
    
    
    
class MrpWorkorder(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.workorder'
    
    oa_id = fields.Many2one('sale.order', related='production_id.oa_id', string='OA', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', related='production_id.sale_order_line', string='Sale Order Line', store=True, readonly=True)
    
    daily_qty_produced = fields.Float(
        'Quantity Produced', default=0.0,
        digits='Product Unit of Measure', compute="_compute_daily_produced",
        copy=False)
    
    @api.depends('time_ids.qty_produced', 'daily_qty_produced')
    def _compute_daily_produced(self):
        for order in self:
            order.daily_qty_produced = sum(order.time_ids.mapped('qty_produced'))
        
    
class MrpWoProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"
    
    qty_produced = fields.Float(
        'Quantity Produced', default=0.0,
        digits='Product Unit of Measure',
        copy=False)