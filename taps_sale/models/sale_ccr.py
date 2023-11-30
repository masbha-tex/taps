from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import re
from decimal import Decimal, ROUND_HALF_UP
import decimal
from werkzeug.urls import url_encode
import logging


class SaleCcr(models.Model):
    _name = 'sale.ccr'
    _description = 'CCR COMPLAINT'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc'
    _check_company_auto = True
    
    # def dynamic_selection(self):
    #     # self.dynamic_selection_onchange(15328)
    #     raise UserError((self.oa_number.id))
    #     order = self.oa_number.id
    #     if order:
    #         result = self.dynamic_selection_onchange(order)
    #     else:
    #         result = False
    #     return result


        

    # @api.onchange('oa_number')
    # def dynamic_selection_onchange(self, id):
        

    
    
        

    name = fields.Char(string='CCR')
    oa_number = fields.Many2one('sale.order', string='OA Number')
    customer = fields.Many2one('res.partner',related = 'oa_number.partner_id', string='Customer')
    buyer = fields.Many2one('res.partner',related = 'oa_number.buyer_name', string='Buyer')
    pi_number = fields.Many2one('sale.order', related = 'oa_number.order_ref',string='PI Number')
    order_quantity = fields.Float(related = 'oa_number.order_ref.total_product_qty',string='Order Quantity')
    rejected_quantity = fields.Float(string='Rejected Quantity')
    complaint = fields.Text(string='Complaint/Defeat')
    department_id = fields.Many2one('hr.department', domain="[('parent_id', '=', False)]" ,string='Responsible Department')
    replacement_quantity = fields.Float(string='Replacement Quantity')
    analysis_activity = fields.Text(string='Analysis Activity')
    currective_action = fields.Text(string='Currective Action')
    preventive_action = fields.Text(string='Preventive Action')
    # fg_product = fields.Selection(selection=lambda self: self.dynamic_selection(), string="Fg Product")
    
    sale_order_line_id = fields.Many2many('sale.order.line', string="Sale Order Line")
    fg_product = fields.Selection(selection="_compute_selection", string="Fg Products")
    
    state = fields.Selection(
        [('justified','Justified'),
         ('notjustified','Not Justified')],
        'State', store=True)


    # @api.onchange('oa_number')
    # def _onchange_oa_number(self):
    #     if self.oa_number:
    #         sale_order_lines = self.env['sale.order.line'].search([
    #             ('order_id', '=', self.oa_number.id),
    #         ])
    #         self.sale_order_line_id = [(6, 0, sale_order_lines.ids)]

    #         # Update the domain for fg_product based on the products in sale_order_lines
    #         product_ids = sale_order_lines.mapped('product_id')
    #         return {'domain': {'fg_product': [('id', 'in', product_ids)]}}
    #     else:
    #         self.sale_order_line_id = False
    #         return {'domain': {'fg_product': []}}
    
    def _compute_selection(self):
        # raise UserError((self))
        selection = set()
        sale_order_lines = self.env['sale.order.line'].search([])
        for order in sale_order_lines:
            selection.add((str(order.product_template_id.id), str(order.product_template_id.name)))
    
        return list(selection)
    @api.onchange('oa_number')
    def _compute_selection_onchange(self):
        # raise UserError((self))
        # selection = set()
        selection = []
        sale_order_lines = self.env['sale.order.line'].search([('order_id','=', self.oa_number.id)])
        self.sale_order_line_id = [(6, 0, sale_order_lines.ids)]
        product_template_ids = sale_order_lines.mapped('product_template_id.id')
        return {'domain': {'fg_product': [('product_template_id.id', 'in', product_template_ids)]}}
        # for order in sale_order_lines:
            # selection.add((order.product_template_id.id, order.product_template_id.name))
            # selection += [('%s' % order.product_template_id.name, '%s' % order.product_template_id.)]
        # self.fg_product = (selection)
        # return list(selection)


    # @api.depends('oa_number')
    # def change_sel(self):
    #     if self.oa_number:
    #         # sale_order_lines = self.env['sale.order.line'].search([('order_id', '=', self.oa_number.id)])
    #         # raise UserError((self))
    #         self.fg_product = [('', ''),('transfer', 'Bank transfer')]
        
        

