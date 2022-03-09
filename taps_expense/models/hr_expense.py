# -*- coding: utf-8 -*-

from odoo.tools.float_utils import float_round as round

from odoo import models, fields, api
from datetime import timedelta, datetime, time
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import format_date
import calendar
from odoo.exceptions import UserError, ValidationError
import math

class taps_expense(models.Model):
    _inherit = 'hr.expense'
    
    expense_line = fields.One2many('hr.expense.line', 'line_id', string='Expense Lines', copy=True)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Expense to Vendor")
    ], default='own_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")
    previous_balance = fields.Float("Previous Balance", store=False, compute='_compute_advance', digits='Account')
    advance_amount = fields.Float("Budget Amount", store=False, compute='_compute_advance', digits='Account')
    used_amount = fields.Float("Total Expensed", store=False, compute='_compute_advance', digits='Account')
    balance_amount = fields.Float("Balance Amount", store=False, compute='_compute_advance', digits='Account')

    
    @api.depends('expense_line.amount')
    def _amount_all(self):
        for expense in self:
            amount_untaxed = amount_tax = 0.0
            for line in expense.expense_line:
                #line._compute_amount()
                amount_untaxed += line.amount
                amount_tax += line.price_tax
            currency = expense.currency_id #or expense.partner_id.property_purchase_currency_id or self.env.company.currency_id
            expense.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'unit_amount': currency.round(amount_untaxed),
                'total_amount': currency.round(amount_tax),
            })    
    
    
    def float_to_time(self,hours):
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(round(60 * fractional, precision_digits=0)), 0)    
    
    @api.onchange('employee_id', 'date', 'currency_id')
    def _compute_advance(self): #for rec in self:
        
        if self.employee_id:
            prfromdate = self.date.replace(day=1) - relativedelta(months = 1)
            prtodate = prfromdate.replace(day = calendar.monthrange(prfromdate.year, prfromdate.month)[1])
            #raise UserError((pr_fromdate,pr_todate))
            cufromdate = fields.datetime.now().replace(day=1).date()
            cutodate = cufromdate.replace(day = calendar.monthrange(cufromdate.year, cufromdate.month)[1])
            #raise UserError((cu_fromdate,cu_todate))
            hour_from = 0.0
            hour_to = 23.98
            combine = datetime.combine
            
            pr_fromdate = combine(prfromdate, self.float_to_time(hour_from))
            pr_todate = combine(prtodate, self.float_to_time(hour_to))
            
            cu_fromdate = combine(cufromdate, self.float_to_time(hour_from))
            cu_todate = combine(cutodate, self.float_to_time(hour_to))
            
            
            pre_ad_amount = 0
            pre_used_amount = 0
            cr_ad_amount = 0
            cr_used_amount = 0
            
            pre_advance = self.env['hr.imprest'].search([('imprest_employee', '=', self.employee_id.id), ('imprest_date', '>=', pr_fromdate), ('imprest_date', '<=', pr_todate)])
            
            cr_advance = self.env['hr.imprest'].search([('imprest_employee', '=', self.employee_id.id), ('imprest_date', '>=', cu_fromdate), ('imprest_date', '<=', cu_todate)])
            
            
            
            pre_used = self.env['hr.expense'].search([('employee_id', '=', self.employee_id.id), ('date', '>=', pr_fromdate), ('date', '<=', pr_todate), ('currency_id', '=', self.currency_id.id)])
            
            cr_used = self.env['hr.expense'].search([('employee_id', '=', self.employee_id.id), ('date', '>=', cu_fromdate), ('date', '<=', cu_todate), ('currency_id', '=', self.currency_id.id)])
            
            if pre_advance:
                if self.currency_id.name == "USD":
                    pre_ad_amount = sum(pre_advance.mapped('imprest_amount_usd'))
                if self.currency_id.name == "BDT":
                    pre_ad_amount = sum(pre_advance.mapped('imprest_amount_bdt'))
                
            if pre_used:
                    pre_used_amount = sum(pre_used.mapped('total_amount'))
                    

            if cr_advance:
                if self.currency_id.name == "USD":
                    cr_ad_amount = sum(cr_advance.mapped('imprest_amount_usd'))
                if self.currency_id.name == "BDT":
                    cr_ad_amount = sum(cr_advance.mapped('imprest_amount_bdt'))
                
            if cr_used:
                    cr_used_amount = sum(cr_used.mapped('total_amount'))                    
                    
            
            self.previous_balance = pre_ad_amount-pre_used_amount
            self.advance_amount = cr_ad_amount
            self.used_amount = cr_used_amount
            self.balance_amount = cr_ad_amount-cr_used_amount
            
            
            
class ExpenseLine(models.Model):
    _name = 'hr.expense.line'
    _description = 'Expense Details'
    
    
    line_id = fields.Many2one('hr.expense', index=True, required=True, ondelete='cascade')
    
    address_home_id = fields.Many2one(
        'res.partner', 'Address', help='Enter here any kind of contact indivisual/company.',
        groups="hr.group_hr_user", tracking=True, store=True,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    description = fields.Char('Description', store=True)
    
    #amount = fields.Monetary(string='Amount', store=True, digits='Account')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    amount = fields.Monetary(string='Amount', store=True, digits='Account')
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)    
    
    
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all')    
    

    @api.depends('amount', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['amount'],
                vals['currency_id'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'amount': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'amount': self.amount,
            'currency_id': self.line_id.currency_id,
        }