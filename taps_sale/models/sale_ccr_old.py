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



    
class SaleCcrOld(models.Model):
    _name = 'sale.ccr.old'
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
        

    
    
        

    name = fields.Char(string='CCR Reference', required=True, copy=False, index=True)
    oa_number = fields.Char(string='OA Number')
    customer = fields.Char(string='Customer')
    buyer = fields.Char(string='Buyer')
    pi_number = fields.Char(string='PI Number')
    order_quantity = fields.Float(string='Order Quantity')
    rejected_quantity = fields.Float(string='Rejected Quantity')
    ccr_type= fields.Char(string='CCR Type')
    complaint = fields.Text(string='Complaint/Defeat')
    department_id = fields.Char(string='Responsible Department')
    replacement_quantity = fields.Float(string='Replacement Quantity')
    analysis_activity = fields.Text(string='Analysis Activity')
    currective_action = fields.Text(string='Currective Action')
    preventive_action = fields.Text(string='Preventive Action')
    # fg_product = fields.Selection(selection=lambda self: self.dynamic_selection(), string="Fg Product")
    fg_product = fields.Char(string='FG Product')
    finish = fields.Char(string="Finish")
    slider = fields.Char(string="Slider")
    sale_representative = fields.Char(string='Sale Representative')
    team = fields.Char(string='Sales Team')
    team_leader = fields.Char(string='Team Leader')
    company_id = fields.Char(string='Company', store=True, readonly=True, index=True)
    invoice_reference = fields.Char(string='Invoice Ref.')
    report_date = fields.Date(string='Report Date', default= date.today())
    justification_level = fields.Selection(
        [('justified','Justified'),
         ('notjustified','Not Justified')],
        'State', store=True)

    state = fields.Selection([
        ('draft', 'draft'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')


    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.ccr', sequence_date=seq_date) or _('New')
        result = super(SaleCcr, self).create(vals)
        return result

    def action_cancel(self):
        self.write({'state': 'cancel'})
        return {}
    def action_draft(self):
        self.write({'state': 'draft'})
        return {}
    def action_close(self):
        self.write({'state': 'done'})
        return {}

    def action_smart_button(self):
        return {}
   