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
    _name = 'mrp.requisition'
    _description = 'Requisition'
    _check_company_auto = True
    
    item = fields.Text(string='Item', readonly=True)
    shade_finish = fields.Text(string='Shade / Finish', readonly=True)
    work_center = fields.Many2one('mrp.workcenter', string='Requisition For')
    # requisition_for = fields.Selection([
    #     ('dyeing', 'Dyeing'),
    #     ('sliderplating', 'Slider Plating'),
    #     ('topplating', 'Top Plating'),
    #     ('bottomplating', 'Bottom Plating'),
    #     ('pinboxplating', 'Pinbox Plating'),
    #     ('painting', 'Painting'),
    #     ('sliassembly', 'Slider Assembly')],
    #     string='Requisition For')
    material_qty = fields.Float('Material Qty', readonly=True)
    materials_qty = fields.Char('Material Qty.', readonly=True)
    # work_center = fields.Many2one('mrp.workcenter', string='Requisition For') self.work_center.id

    
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company,
        index=True, required=True)
    requisition_line = fields.One2many('mrp.requisition.line', 'requisition_id', readonly=False, string='Requisition Line',copy=True, auto_join=True)
    

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        material_qty = None
        # f"{record.prefix} - {record.float_value}"
        tape = slider = top = bottom = pinbox = wire = 0.0
        if active_model == 'operation.details':
            operation = self.env["operation.details"].browse(active_id)
            
            
            in_len = len(operation)
            i = 0
            all_mrp_lines = ''
            for op in operation:
                if i == in_len-1:
                    all_mrp_lines = all_mrp_lines + op.mrp_lines
                else:
                    all_mrp_lines = all_mrp_lines + op.mrp_lines + ','
                i += 1
            
        
        # all_mrp_lines = ','.join(all_mrp_lines)
        all_mrp_lines_st = str(all_mrp_lines)
        # raise UserError((all_mrp_lines))
        mrp_ids = [int(id_str) for id_str in all_mrp_lines_st.split(',')]
        production = self.env["manufacturing.order"].browse(mrp_ids)
        res["item"] = production[0].fg_categ_type
        # res["item_qty"] = sum(production.mapped('balance_qty'))
        res["shade_finish"] = production[0].shade
        return res 
    
    # @api.onchange('requisition_for')
    # def _onchange_plan(self):
    #     active_id = self.env.context.get("active_ids")
    #     production = self.env["manufacturing.order"].browse(active_id)
    #     if self.plan_for == 'dyeing':
    #         self.material_qty = sum(production.mapped('tape_con'))
    #         self.shade_finish = production[0].shade
    #     elif self.plan_for == 'sliderplating':
    #         self.material_qty = sum(production.mapped('slider_con'))
    #         self.shade_finish = production[0].finish
    #     elif self.plan_for == 'topplating':
    #         self.material_qty = sum(production.mapped('topwire_con'))
    #         self.shade_finish = production[0].finish
    #     elif self.plan_for == 'bottomplating':
    #         self.material_qty = sum(production.mapped('botomwire_con'))
    #         self.shade_finish = production[0].finish
    #     elif self.plan_for == 'sliassembly':
    #         self.material_qty = sum(production.mapped('slider_con'))
    #         self.shade_finish = production[0].finish
            
    def done_mo_requisition(self):
        active_model = self.env.context.get("active_model")
        ope_id = self.env.context.get("active_ids")
        operation = self.env['operation.details'].browse(1)
        return operation.set_requisition(self.company_id.id, active_model,ope_id,self.work_center.id,self.requisition_line)

class MachineLine(models.TransientModel):
    _name = 'mrp.requisition.line'
    _description = 'RM Requisition'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True
    
    sequence = fields.Integer(string='Sequence', default=10)
    requisition_id = fields.Many2one('mrp.requisition', string='Requisition ID', ondelete='cascade', index=True, copy=False)    
    company_id = fields.Many2one(
        'res.company', 'Company',
        default=lambda self: self.env.company,
        index=True, required=True)
    
    product_id = fields.Many2one(
        'product.product', 'Product',
        check_company=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", index=True, required=True)
    # product_tmpl_id = fields.Many2one(
    #     'product.template', 'Product Template',
    #     related='product_id.product_tmpl_id', readonly=True,
    #     help="Technical: used in views")    
    
    product_uom = fields.Many2one('uom.uom', 'Unit of Measure', required=True,
                                  related='product_id.uom_id')
    
    product_qty = fields.Float('Quantity', digits='Product Unit of Measure', required=True)
    
    
#     @api.depends('product_qty')
#     def _compute_qty(self):
#         """
#         Compute the quantity of the Split line.
#         """
#         qty = 0
#         for line in self:
#             qty += line.product_qty
#             line.update({'qty_total': qty})
