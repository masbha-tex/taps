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
    fg_product = fields.Selection([], string="Fg Product")    
    state = fields.Selection(
        [('justified','Justified'),
         ('notjustified','Not Justified')],
        'State', store=True)

    # @api.model
    # def create(self, values):
    #     res = super(SaleCcr, self).create(values)
    #     if vals.get('oa_number'):
        
    #     return res  
    
    # def dynamic_selection(self):
    #     # raise UserError((self.id))
    #     selection= []
    #     selection.append((0, 0))
    #         # raise UserError((self.env['sale.order.line'].search([('order_id','=',order)])))
    #     return selection

    
    @api.depends('oa_number')
    def _compute_fg_product_selection(self):
        selection = []
        order = self.oa_number.id
        raise UseError((self.env['sale.order.line'].search([('order_id', '=', order)])))
        for product in self.env['sale.order.line'].search([('order_id', '=', order)]):
            selection.append((product.product_template_id.id, product.product_template_id.name))
            
            
        return {'value': {'self.fg_product': selection}}
        
        # Add new options to the Selection field
        

        
        

