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

class CcrWizardCa(models.TransientModel):
    _name = 'sale.ccr.wizard.ca'
    _description = 'Take Corrective Action'

    
    ca_step_1 = fields.Char(string='CA Step 1')
    ca_step_2 = fields.Char(string='CA Step 2')
    ca_step_3 = fields.Char(string='CA Step 3')
    ca_closing_date = fields.Date(string="CA Closing", default=date.today())
    after_sales = fields.Selection([
        ('Replacement', 'Replacement'),
        ('Rework', 'Rework'),
    ], string="After sales Service")
    replacement_item = fields.Selection([
        ('Full Zipper', 'Full Zipper'),
        ('Puller', 'Puller'),
        ('Slider', 'Slider'),
        ('Tape', 'Tape'),
        ('Button', 'Button'),
    ], string="Replace/Rework Item")
    replacement_quantity = fields.Float(string="Quantity")
    cost = fields.Float(string="Cost")
    ccr_no = fields.Char(string="CCR", readonly=True)
    ccr_raised_by = fields.Many2one('res.users',string="Raised By", readonly=True)
    customer = fields.Many2one('res.partner',string="Customer", readonly=True)
    buyer = fields.Many2one('res.partner',string="Buyer", readonly=True)
    oa_number = fields.Many2one('sale.order', string='OA Number', readonly=True)
    pi_number = fields.Many2one('sale.order', string='Pi Number', readonly=True)
    invoice_reference = fields.Char(string="Invoice Ref.", readonly=True)
    ccr_type= fields.Many2one('sale.ccr.type',string='CCR Type', readonly=True)
    analysis_activity = fields.Text(string='Probable Root Cause/Analysis', readonly=True)

    def action_corrective(self):
        # raise UserError((self.env.context.get('active_id')))
        ccr = self.env['sale.ccr'].search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({
            'ca_step_1': self.ca_step_1,
            'ca_step_2': self.ca_step_2,
            'ca_step_3': self.ca_step_3,
            'ca_closing_date':self.ca_closing_date,
            'after_sales': self.after_sales,
            'replacement_item': self.replacement_item,
            'replacement_quantity': self.replacement_quantity,
            'cost' : self.cost,
            'states':'ca'})
        return {}

    def cancel(self):
        return {}
        
class CcrWizardPa(models.TransientModel):
    _name = 'sale.ccr.wizard.pa'
    _description = 'Take Preventive Action'

    pa_step_1 = fields.Char(string='PA Step 1')
    pa_step_2 = fields.Char(string='PA Step 2')
    pa_step_3 = fields.Char(string='PA Step 3')
    pa_closing_date = fields.Date(string="PA Closing", default=date.today())
    ccr_no = fields.Char(string="CCR", readonly=True)
    ccr_raised_by = fields.Many2one('res.users',string="Raised By", readonly=True)
    customer = fields.Many2one('res.partner',string="Customer", readonly=True)
    buyer = fields.Many2one('res.partner',string="Buyer", readonly=True)
    oa_number = fields.Many2one('sale.order', string='OA Number', readonly=True)
    pi_number = fields.Many2one('sale.order', string='Pi Number', readonly=True)
    invoice_reference = fields.Char(string="Invoice Ref.", readonly=True)
    ccr_type= fields.Many2one('sale.ccr.type',string='CCR Type', readonly=True)
    analysis_activity = fields.Text(string='Probable Root Cause/Analysis', readonly=True)
    ca_step_1 = fields.Char(string='CA Step 1', readonly=True)
    ca_step_2 = fields.Char(string='CA Step 2', readonly=True)
    ca_step_3 = fields.Char(string='CA Step 3', readonly=True)
    ca_closing_date = fields.Date(string="CA Closing", readonly=True)
    after_sales = fields.Char('After Sales Service', readonly=True)
    replacement_item = fields.Char('Replacement Item', readonly=True)
    replacement_quantity= fields.Float(string='Replacement Quantity', readonly=True)
    cost= fields.Float(string='Cost', readonly=True)

    def action_preventive(self):
        # raise UserError((self.env.context.get('active_id')))
        ccr = self.env['sale.ccr'].search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({
            # 'preventive_action': self.preventive_action,
            'pa_step_1': self.pa_step_1,
            'pa_step_2': self.pa_step_2,
            'pa_step_3': self.pa_step_3,
            'pa_closing_date' : self.pa_closing_date,
            'states':'pa'})
        
        email_from_list=['odoo@texzipperbd.com']
        
        # if ccr.company_id.id == 1:
        #     email_from_list.append('qa@bd.texfasteners.com')
        # if ccr.company_id.id == 3:
        #     email_from_list.append('quality2.metaltrims@texzipperbd.com')
            
        template_id = self.env.ref('taps_sale.ccr_assign_manufacturing_confirmation_template')
        if template_id:
            template_id.write({
                'email_to': 'nitish.bassi@texzipperbd.com',
                'email_from': email_from_list,
                'email_cc' : 'asraful.haque@texzipperbd.com',
            })
            
            template_id.send_mail(ccr.id, force_send=False)
            
    def cancel(self):
        return {}

class CcrWizardnot(models.TransientModel):
    _name = 'sale.ccr.wizard.notjustify'
    _description = 'CCR Wizard Not Justify'
    
    reason = fields.Text(string="Reason for Not justify")
    non_justify_action = fields.Text(string="Action to be taken")

    def action_notjustify(self):
        ccr = self.env['sale.ccr'].sudo().search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({
            'reason': self.reason,
            'states': 'nonjust',
            'justification' : 'Not Justified',
            'non_justify_action' : self.non_justify_action
                   })
        
        email_from_list=['odoo@texzipperbd.com']
        
        # if ccr.company_id.id == 1:
        #     email_from_list.append('qa@bd.texfasteners.com')
        # if ccr.company_id.id == 3:
        #     email_from_list.append('quality2.metaltrims@texzipperbd.com')
            
        template_id = self.env.ref('taps_sale.ccr_assign_manufacturing_confirmation_template')
        if template_id:
            template_id.write({
                'email_to': 'nitish.bassi@texzipperbd.com',
                'email_from': email_from_list,
                'email_cc' : 'asraful.haque@texzipperbd.com',
            })
            
            template_id.send_mail(ccr.id, force_send=False)
        

    def cancel(self):
        return {}
        


