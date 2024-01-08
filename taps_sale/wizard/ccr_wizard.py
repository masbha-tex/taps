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

    
    corrective_action = fields.Text(string='Currective Action')
    ca_closing_date = fields.Date(string="CA Closing", default=date.today())
    after_sales = fields.Selection([
        ('replace', 'Replacement'),
        ('rework', 'Rework'),
    ], string="After sales Service")
    replacement_quantity = fields.Float(string="Quantity")
    cost = fields.Float(string="Cost")

    def action_corrective(self):
        # raise UserError((self.env.context.get('active_id')))
        ccr = self.env['sale.ccr'].search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({
            'corrective_action': self.corrective_action,
            'ca_closing_date':self.ca_closing_date,
            'after_sales': self.after_sales,
            'replacement_quantity': self.replacement_quantity,
            'cost' : self.cost,
            'states':'ca'})
        return {}

    def cancel(self):
        return {}
        
class CcrWizardPa(models.TransientModel):
    _name = 'sale.ccr.wizard.pa'
    _description = 'Take Preventive Action'

    preventive_action = fields.Text(string='Preventive Action')
    pa_closing_date = fields.Date(string="PA Closing", default=date.today())

    def action_preventive(self):
        # raise UserError((self.env.context.get('active_id')))
        ccr = self.env['sale.ccr'].search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({
            'preventive_action': self.preventive_action,
            'pa_closing_date' : self.pa_closing_date,
            'states':'pa'})
        template_id = self.env.ref('taps_sale.ccr_assign_manufacturing_confirmation_template')
        if template_id:
            template_id.write({
                'email_to': 'asraful.haque@texzipperbd.com',
                'email_from': 'asraful.haque@texzipperbd.com',
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
        # email_cc_list=['alamgir@texzipperbd.com','nitish.bassi@texzipperbd.com']
        # email_to_list=[]
        # email_from_list=[]
        # if self.company_id.id == 1:
        #     email_cc_list.append('ranjeet.singh@texzipperbd.com')
        #     email_to_list.append('qa@bd.texfasteners.com')
        #     email_from_list.append('csd.zipper@texzipperbd.com')
        # if self.company_id.id == 3:
        #     email_cc_list.append('kumar.abhishek@texzipperbd.com')
        #     email_to_list.append('quality2.metaltrims@texzipperbd.com')
        #     email_from_list.append('nasir.csd@texzipperbd.com')
        # email_cc = ','.join(email_cc_list)
        # email_to = ','.join(email_to_list)
        # email_from = ','.join(email_from_list)
        template_id = self.env.ref('taps_sale.ccr_assign_manufacturing_confirmation_template')
        if template_id:
            template_id.write({
                'email_to': 'asraful.haque@texzipperbd.com',
                'email_from': 'asraful.haque@texzipperbd.com',
                'email_cc' : 'asraful.haque@texzipperbd.com',
            })
            
            template_id.send_mail(ccr.id, force_send=False)
        

    def cancel(self):
        return {}
        


