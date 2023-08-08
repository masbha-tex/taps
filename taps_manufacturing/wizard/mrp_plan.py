import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import _, api, fields, models
import math

from typing import List, Union

_logger = logging.getLogger(__name__)


class ManufacturingPlan(models.TransientModel):
    _name = 'mrp.plan'
    _description = 'Manufacturing Plan'
    _check_company_auto = True

    item = fields.Text(string='Item', readonly=True)
    shade_finish = fields.Text(string='Shade / Finish', readonly=True)
    plan_for = fields.Selection([
        ('dyeing', 'Dyeing'),
        ('sliderplating', 'Slider Plating'),
        ('topplating', 'Top Plating'),
        ('bottomplating', 'Bottom Plating'),
        ('pinboxplating', 'Pinbox Plating'),
        ('painting', 'Painting'),
        ('sliassembly', 'Slider Assembly')],
        string='Plan For')
    
    plan_start = fields.Datetime(string='Start Date', required=True)
    plan_end = fields.Datetime(string='End Date')
    item_qty = fields.Float('Item Qty',digits='Product Unit of Measure', readonly=True)
    material_qty = fields.Float('Material Qty',digits='Product Unit of Measure', readonly=True)
    plan_qty = fields.Float(string='Qty', store=True, default=0.0, digits='Product Unit of Measure')
    
    machine_line = fields.One2many('machine.line', 'plan_id', string='Machines',copy=True, auto_join=True)
    

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        #raise UserError((active_id))
        
        # Auto-complete production_id from context
        #if "mo_id" in fields_list and active_model == "mrp.production":
        # res["item_qty"] = active_id
        production = self.env["manufacturing.order"].browse(active_id)
        res["item"] = production[0].fg_categ_type
        res["item_qty"] = sum(production.mapped('balance_qty'))
            #raise UserError((active_id))
            #if production.product_tracking == "serial":
                
        # # Auto-complete split_qty from production_id
        # if "split_qty" in fields_list and res.get("production_id"):
        #     production = self.env["mrp.production"].browse(res["production_id"])
        #     res["split_qty"] = production._get_quantity_to_backorder()
        return res 
    
    @api.onchange('plan_for')
    def _onchange_plan(self):
        active_id = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(active_id)
        if self.plan_for == 'dyeing':
            self.material_qty = sum(production.mapped('tape_con'))
            self.shade_finish = production[0].shade
        elif self.plan_for == 'sliderplating':
            self.material_qty = sum(production.mapped('slider_con'))
            self.shade_finish = production[0].finish
        elif self.plan_for == 'topplating':
            self.material_qty = sum(production.mapped('topwire_con'))
            self.shade_finish = production[0].finish
        elif self.plan_for == 'bottomplating':
            self.material_qty = sum(production.mapped('botomwire_con'))
            self.shade_finish = production[0].finish
        elif self.plan_for == 'sliassembly':
            self.material_qty = sum(production.mapped('slider_con'))
            self.shade_finish = production[0].finish
            
    def done_mo_plan(self):
        # if  self.plan_qty > self.material_qty:
        #     raise UserError(('Split quantity should not greterthen the base quantity'))
        #     return
        mo_ids = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(mo_ids)
        production.set_plan(mo_ids,self.plan_for,self.plan_start,self.plan_end,self.plan_qty,self.machine_line)
        #production.set_operation(mo_ids,self.plan_for,self.machine_line)
        return 


class MachineLine(models.TransientModel):
    _name = 'machine.line'
    _description = 'Machine wise plan'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True
    
    sequence = fields.Integer(string='Sequence', default=10)
    plan_id = fields.Many2one('mrp.plan', string='Plan ID', ondelete='cascade', index=True, copy=False)
    machine_no = fields.Selection([
        ('m1', 'M/C 1'),
        ('m2', 'M/C 2'),
        ('m3', 'M/C 3'),
        ('m4', 'M/C 4')],
        string='Machine No', domain=[('plan_for', '=', 'dyeing')])
    material_qty = fields.Float('Quantity',default=1.0, digits='Product Unit of Measure',required=True)
    
    
#     @api.depends('product_qty')
#     def _compute_qty(self):
#         """
#         Compute the quantity of the Split line.
#         """
#         qty = 0
#         for line in self:
#             qty += line.product_qty
#             line.update({'qty_total': qty})
