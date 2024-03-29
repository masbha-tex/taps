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
    material_name = fields.Text(string='Material', readonly=True)
    plan_for = fields.Many2one('mrp.workcenter', required=True, string='Plan For', help="Assign to")
    material = fields.Selection([
        ('tape', 'Tape'),
        ('slider', 'Slider'),
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('pinbox', 'Pinbox')],
        string='Material Type', required=True)
    
    plan_start = fields.Datetime(string='Start Date', required=True, default=datetime.now())
    plan_end = fields.Datetime(string='End Date')
    item_qty = fields.Float('Item Qty',digits='Product Unit of Measure', readonly=True)
    material_qty = fields.Float('Material Qty',digits='Product Unit of Measure', readonly=True)
    common_machine = fields.Boolean(readonly=False, string='Same Machine', default=False)
    full_qty = fields.Boolean(readonly=False, string='Full Qty', default=False)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    create_mr = fields.Boolean(readonly=False, string='Create MR', default=False)
    product_id = fields.Many2one('product.product', 'Raw Material', check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True)
    product_uom = fields.Many2one('uom.uom', 'Unit', related='product_id.uom_id')
    stock_qty = fields.Float('Available', digits='Product Unit of Measure')
    

    @api.depends('machine_line.material_qty')
    def _compute_plan_qty(self):
        for plan in self:
            plan.plan_qty = sum(line.material_qty for line in plan.machine_line)
    
    plan_qty = fields.Float(string='Plan Qty', readonly=False, store=True, default=0.0, digits='Product Unit of Measure', compute='_compute_plan_qty')
    
    machine_line = fields.One2many('machine.line', 'plan_id', string='Machines',copy=True, auto_join=True)

    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        production = self.env[""+active_model+""].browse(active_id)
        res["item"] = production[0].fg_categ_type
        res["item_qty"] = sum(production.mapped('balance_qty'))
        return res
    
    @api.onchange('common_machine')
    def _onchange_selection(self):
        if self.common_machine:
            if self.machine_line:
                m_no = self.mapped('machine_line.machine_no.id')
                if m_no:
                    self.machine_line.update({'machine_no':m_no[0]})
                else:
                    self.common_machine = False
                    raise UserError(('Select atleast one machine'))
            else:
                self.common_machine = False
                raise UserError(('Machine Required'))
                

    @api.onchange('full_qty')
    def _onchange_qty_selection(self):
        if self.full_qty:
            if self.machine_line:
                for ml in self.machine_line:
                    if ml.qty_balance>0 and ml.machine_no:
                        l_lots = math.ceil(ml.qty_balance/ml.machine_no.capacity)
                        ml.update({'material_qty':ml.qty_balance,'lots':l_lots})
                    else:
                        raise UserError(('Machine and Quantity Required'))
                    
            else:
                self.plan_qty = self.material_qty
                
    @api.onchange('plan_for')
    def _onchange_qty(self):
        # raise UserError((self.plan_for.name))
        if self.plan_for.name == 'Dyeing':
            self.material = 'tape'
            
            active_model = self.env.context.get("active_model")
            active_id = self.env.context.get("active_ids")
            production = self.env[""+active_model+""].browse(active_id)
            
            oa_ids = production.mapped('oa_id')
            oa_ids = list(set(oa_ids))
            
            planline_values = []
    
            for oa in oa_ids:
                oa_det = production.filtered(lambda op: op.oa_id.id == int(oa[0]))
                oa_total = sum(oa_det.mapped('tape_con'))
                balance_total = sum(oa_det.mapped('dyeing_plan_due'))
                planline_values.append((0, 0, {
                    'sequence': 10,
                    'oa_id': int(oa[0]),
                    'sa_oa_ref': oa_det[0].shade_ref,
                    'actual_qty': oa_total,
                    'qty_balance': balance_total,
                    'machine_no': None,
                    'reserved': None,
                    'lots': None,
                    'material_qty': None,
                    'remarks': None
                    }))
                
            self.update({'machine_line': planline_values,})
        elif self.plan_for.name == 'Plating':
            self.material = 'slider'
            self.machine_line.unlink()
        elif self.plan_for.name == 'Painting':
            self.material = 'slider'
            self.machine_line.unlink()
        else:
            self.material = None
            self.machine_line.unlink()
            

    @api.onchange('material')
    def _onchange_plan(self):
        active_id = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(active_id)
        #raise UserError((self.plan_for))
        if self.material == 'tape':
            self.material_qty = round(sum(production.mapped('tape_con')),2) - round(sum(production.mapped('dyeing_plan_qty')),2)
            self.shade = production[0].shade
            self.material_name = production[0].dyedtape
        elif self.material == 'slider':
            self.material_qty = round(sum(production.mapped('slider_con')),0) - round(sum(production.mapped('plating_plan_qty')),0)
            self.finish = production[0].finish
            self.material_name = production[0].slidercodesfg
        elif self.material == 'top':
            self.material_qty = round(sum(production.mapped('topwire_con')),2) - round(sum(production.mapped('top_plat_plan_qty')),2)
            self.finish = production[0].finish
            self.material_name = production[0].ptopfinish
        elif self.material == 'bottom':
            self.material_qty = round(sum(production.mapped('botomwire_con')),2) - round(sum(production.mapped('bot_plat_plan_qty')),2)
            self.finish = production[0].finish
            self.material_name = production[0].pbotomfinish
        elif self.material == 'pinbox':
            self.material_qty = round(sum(production.mapped('pinbox_con')),0) - round(sum(production.mapped('pin_plat_plan_qty')),0)
            self.finish = production[0].finish
            self.material_name = production[0].ppinboxfinish
        elif self.plan_for.name == 'Slider assembly':
            self.material_qty = round(sum(production.mapped('slider_con')),0) - round(sum(production.mapped('sli_asmbl_plan_qty')),0)
            self.finish = production[0].finish
            self.material_name = production[0].slidercodesfg
         
    def done_mo_plan(self):
        # if  self.plan_qty > self.material_qty:
        #     raise UserError(('Split quantity should not greterthen the base quantity'))
        #     return
        
        mo_ids = self.env.context.get("active_ids")
        production = self.env["manufacturing.order"].browse(mo_ids)
        if self.create_mr:
            production.set_plan(mo_ids,self.plan_for.id,self.plan_for,self.material,self.plan_start,
                            self.plan_end,self.plan_qty,self.machine_line,self.product_id)
        else:
            production.set_plan(mo_ids,self.plan_for.id,self.plan_for,self.material,self.plan_start,
                            self.plan_end,self.plan_qty,self.machine_line,None)
        #production.set_operation(mo_ids,self.plan_for,self.machine_line)
        return 


class MachineLine(models.TransientModel):
    _name = 'machine.line'
    _description = 'Machine wise plan'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True


    sequence = fields.Integer(string='Sequence')
    plan_id = fields.Many2one('mrp.plan', string='Plan ID', ondelete='cascade')
    oa_id = fields.Many2one('sale.order', string='OA', store=True)
    sa_oa_ref = fields.Text(string='OA/SA Ref.', readonly=False, store=True)
    actual_qty = fields.Float('Actual Qty',digits='Product Unit of Measure')
    qty_balance = fields.Float('Balance',digits='Product Unit of Measure')
    machine_no = fields.Many2one('machine.list', string='Machine No')
    reserved = fields.Integer('Reserved Lots')
    lots = fields.Integer(string='Lots')
    material_qty = fields.Float('Quantity',digits='Product Unit of Measure')
    remarks = fields.Text(string='Remarks')


    @api.model
    def duplicate_line(self):
        raise UserError(('thgrfr'))
        max_seq = max(line.sequence for line in self.plan_id.machine_line)
        self.copy({'plan_id': self.plan_id.id, 'sequence': max_seq + 1})


    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Set default values for fields in SizewiseLotLine
        res.update({
            'sequence': None,
            'oa_id': None,
            'sa_oa_ref': None,
            'actual_qty': None,  # Default Tape C. Value
            'qty_balance': None,  # Default Qty Value
            'machine_no':None,
            'reserved':None,
            'lots':None,
            'material_qty':None,
            'remarks': None
        })

        return res

    # @api.onchange('lots')
    # def _get_qty_bylots(self):
    #     for l in self:
    #         l_qty = l.machine_no.capacity * l.lots
    #         if l.plan_id.material_qty < l_qty:
    #             l_qty = l.plan_id.material_qty
    #         if (l.plan_id.plan_qty + l_qty) > l.plan_id.material_qty:
    #             ext_qty = (l.plan_id.plan_qty + l_qty) - l.plan_id.material_qty
    #             l_qty = l_qty-ext_qty
                
    #         l.material_qty = round(l_qty,2)
    
    @api.onchange('material_qty')
    def _get_qty_bylots(self):
        for l in self:
            if l.machine_no.capacity > 0:
                l_lots = math.ceil(l.material_qty/l.machine_no.capacity)
                l.lots = l_lots
            

    @api.onchange('machine_no')
    def _get_reserved_qty(self):
        for l in self:
            production = self.env["operation.details"].search([('machine_no','=',l.machine_no.id),('operation_of','in',('lot','output')),('state','!=','done')])

            operation = production.filtered(lambda op: op.action_date.date() == self.plan_id.plan_start.date() and 'Output' in op.next_operation)
            if l.machine_no.capacity:
                l.reserved = math.ceil(sum(operation.mapped('balance_qty'))/l.machine_no.capacity)
    
    # @api.model
    # def duplicate_line(self):
    #     max_seq = max(line.sequence for line in self.plan_id.machine_line)
    #     self.copy({'plan_id': self.plan_id.id, 'sequence': max_seq + 1})
        # for record in self:
        #     raise UserError(('fefefe'))
        #     max_seq = max(line.sequence for line in self.plan_id.machine_line)
        #     # self.copy({'plan_id': self.plan_id.id, 'sequence': max_seq + 1})
        #     orderline_values = []
        #     orderline_values.append((0, 0, {
        #         'sequence':max_seq,
        #         'plan_id':self.plan_id,
        #         'oa_id':self.oa_id.id,
        #         'sa_oa_ref':self.sa_oa_ref,
        #         'actual_qty':self.actual_qty,
        #         'qty_balance':self.qty_balance,
        #         'machine_no':self.machine_no.id,
        #         'reserved':self.reserved,
        #         'lots':self.lots,
        #         'material_qty':self.material_qty,
        #         'remarks':self.remarks
        #     }))
        #     self.plan_id.update({'machine_line': orderline_values,})

            
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
