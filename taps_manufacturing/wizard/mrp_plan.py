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
    shade = fields.Text(string='Shade', readonly=True)
    finish = fields.Text(string='Finish', readonly=True)
    plan_for = fields.Many2one('mrp.workcenter', required=True, string='Plan For', help="Assign to")
    material = fields.Selection([
        ('tape', 'Tape'),
        ('slider', 'Slider'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('pinbox', 'Pinbox')],
        string='Material', required=True)
    
    plan_start = fields.Datetime(string='Start Date', required=True, default=datetime.now())
    plan_end = fields.Datetime(string='End Date')
    item_qty = fields.Float('Item Qty',digits='Product Unit of Measure', readonly=True)
    material_qty = fields.Float('Material Qty',digits='Product Unit of Measure', readonly=True)

    @api.depends('machine_line.material_qty')
    def _compute_plan_qty(self):
        for plan in self:
            plan.plan_qty = sum(line.material_qty for line in plan.machine_line)
    
    plan_qty = fields.Float(string='Plan Qty', readonly=False, store=True, default=0.0, digits='Product Unit of Measure', compute='_compute_plan_qty')
    
    machine_line = fields.One2many('machine.line', 'plan_id', string='Machines',copy=True, auto_join=True)


# , inverse='_inverse_plan_qty'

    @api.model
    def default_get(self, fields_list):
        #selected_companies = self.env['res.company'].browse(self._context.get('allowed_company_ids'))
        # raise UserError((self.env['res.company'].browse(self._context.get('allowed_company_ids')).ids))
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        # Auto-complete production_id from context
        #if "mo_id" in fields_list and active_model == "mrp.production":
        # res["item_qty"] = active_id
        production = self.env[""+active_model+""].browse(active_id)
        res["item"] = production[0].fg_categ_type
        res["item_qty"] = sum(production.mapped('balance_qty'))
        return res
    
    def _inverse_plan_qty(self):
        pass    
    
    @api.onchange('plan_for')
    def _onchange_qty(self):
        # raise UserError((self.plan_for.name))
        if self.plan_for.name == 'Dyeing':
            self.material = 'tape'


    @api.onchange('material')
    def _onchange_plan(self):
        active_id = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(active_id)
        #raise UserError((self.plan_for))
        if self.material == 'tape':
            self.material_qty = round(sum(production.mapped('tape_con')),2)
            self.shade = production[0].shade
        elif self.material == 'slider':
            self.material_qty = round(sum(production.mapped('slider_con')),2)
            self.finish = production[0].finish
        elif self.material == 'top':
            self.material_qty = round(sum(production.mapped('topwire_con')),2)
            self.finish = production[0].finish
        elif self.material == 'bottom':
            self.material_qty = round(sum(production.mapped('botomwire_con')),2)
            self.finish = production[0].finish
        elif self.material == 'pinbox':
            self.material_qty = round(sum(production.mapped('pinbox_con')),2)
            self.finish = production[0].finish
        elif self.plan_for.name == 'Slider assembly':
            self.material_qty = round(sum(production.mapped('slider_con')),2)
            self.finish = production[0].finish            
         
    def done_mo_plan(self):
        # if  self.plan_qty > self.material_qty:
        #     raise UserError(('Split quantity should not greterthen the base quantity'))
        #     return
        
        mo_ids = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(mo_ids)
        
        production.set_plan(mo_ids,self.plan_for.id,self.plan_for.name,self.material,self.plan_start,
                            self.plan_end,self.plan_qty,self.machine_line)
        #production.set_operation(mo_ids,self.plan_for,self.machine_line)
        return 


class MachineLine(models.TransientModel):
    _name = 'machine.line'
    _description = 'Machine wise plan'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True
    
    sequence = fields.Integer(string='Sequence', default=10)
    plan_id = fields.Many2one('mrp.plan', string='Plan ID', ondelete='cascade', index=True, copy=False)

    # oa_id = fields.Many2one('sale.order', string='OA', store=True)
    # qty_balance = fields.Float('Balance',default=1.0, digits='Product Unit of Measure')
    machine_no = fields.Many2one('machine.list', string='Machine No', required=True)
    # reserved = fields.Float('Reserved',default=1.0, digits='Product Unit of Measure')
    lots = fields.Integer(string='Lots', required=True)
    material_qty = fields.Float('Quantity',default=1.0, digits='Product Unit of Measure',required=True)
    

    @api.onchange('lots')
    def _get_qty_bylots(self):
        for l in self:
            l_qty = l.machine_no.capacity * l.lots
            if l.plan_id.material_qty < l_qty:
                l_qty = l.plan_id.material_qty
            if (l.plan_id.plan_qty + l_qty) > l.plan_id.material_qty:
                ext_qty = (l.plan_id.plan_qty + l_qty) - l.plan_id.material_qty
                l_qty = l_qty-ext_qty
                
            l.material_qty = round(l_qty,2)

            #l.plan_id.material_qty

            

#     @api.depends('product_qty')
#     def _compute_qty(self):
#         """
#         Compute the quantity of the Split line.
#         """
#         qty = 0
#         for line in self:
#             qty += line.product_qty
#             line.update({'qty_total': qty})
