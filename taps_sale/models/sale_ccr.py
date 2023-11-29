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

    def dynamic_selection(self):
        raise UserError((self))
        selection=[]
        
        for product in self.env['sale.order.line'].search([('order_id','=', 1)]):
            selection += [('%s'% product.product_template_id, '%s'% product.product_template_id)]
        return selection

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
    fg_product = fields.Selection(selection=lambda self: self.dynamic_selection(), string="Fg Product")
    state = fields.Selection(
        [('justified','Justified'),
         ('notjustified','Not Justified')],
        'State', store=True)
        

