# -*- coding: utf-8 -*-

from odoo import models, fields, api


class taps_expense(models.Model):
    _inherit = 'hr.expense'
    
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Expense to Vendor")
    ], default='own_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")