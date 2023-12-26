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

class CcrWizard(models.TransientModel):
    _name = 'sale.ccr.wizard'
    _description = 'CCR Wizard'

    
    corrective_action = fields.Text(string='Currective Action')
    preventive_action = fields.Text(string='Preventive Action')
    ca_closing_date = fields.Date(string="CA Closing", default=date.today())


    
    def action_capa(self):
        # raise UserError((self.env.context.get('active_id')))
        ccr = self.env['sale.ccr'].sudo().search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({'corrective_action': self.corrective_action,'preventive_action': self.preventive_action,'ca_closing_date':self.ca_closing_date,'states':'just'})
        return {}

    def cancel(self):
        return {}


class CcrWizardnot(models.TransientModel):
    _name = 'sale.ccr.wizard.notjustify'
    _description = 'CCR Wizard Not Justify'
    
    reason = fields.Char(string="Reason for Not justify")

    def action_notjustify(self):
        ccr = self.env['sale.ccr'].sudo().search([('id', '=', self.env.context.get('active_id'))])
        ccr.update({'reason': self.reason,'states': 'nonjust'})
        return {}

    def cancel(self):
        return {}
        


