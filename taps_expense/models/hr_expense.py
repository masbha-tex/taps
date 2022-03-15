# -*- coding: utf-8 -*-

from odoo.tools.float_utils import float_round as round

from odoo import models, fields, api, _
from datetime import timedelta, datetime, time
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import format_date
import calendar
from odoo.exceptions import UserError, ValidationError
import math

class taps_expense(models.Model):
    _inherit = 'hr.expense'

    @api.model
    def create(self, vals):
        #if vals.get('name', _('New')) == _('New'):
        if vals.get('name', 'New') == 'New':
            #course_date = vals.get('course_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.expense.name')
        return super(taps_expense, self).create(vals)    
    
    @api.depends('product_id', 'company_id')
    def _compute_from_product_id_company_id(self):
        for expense in self.filtered('product_id'):
            expense = expense.with_company(expense.company_id)
            #expense.name = expense.name or expense.product_id.display_name
            if not expense.attachment_number or (expense.attachment_number and not expense.unit_amount):
                expense.unit_amount = expense.amount_total#expense.product_id.price_compute('standard_price')[expense.product_id.id]
            expense.product_uom_id = expense.product_id.uom_id
            expense.tax_ids = expense.product_id.supplier_taxes_id.filtered(lambda tax: tax.company_id == expense.company_id)  # taxes only from the same company
            account = expense.product_id.product_tmpl_id._get_product_accounts()['expense']
            if account:
                expense.account_id = account
                
    @api.depends('expense_line.price_total')
    def _amount_all(self):
        for expense in self:
            amount_untaxed = amount_tax = 0.0
            for line in expense.expense_line:
                line._compute_amount()
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            currency = expense.currency_id or self.env.company.currency_id
            expense.update({
                'amount_untaxed': currency.round(amount_untaxed),
                'amount_tax': currency.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
                'unit_amount': currency.round(amount_untaxed + amount_tax),
                'total_amount': currency.round(amount_untaxed + amount_tax),
            })
    
    @api.model
    def _default_product_uom_id(self):
        return self.env['uom.uom'].search([], limit=1, order='id')    

    
    #name = fields.Char('Code', store=True, readonly=True, default='New')#default=_('New')
    name = fields.Char('Expense Reference', required=True,  readonly=True, index=True, copy=False, default='New')
    purpose = fields.Char('Description', store=True, required=False, readonly=False)
    
    product_uom_id = fields.Many2one('uom.uom', required=False, string='Unit of Measure',readonly=True, compute='_compute_from_product_id_company_id',
        store=True, 
        default=_default_product_uom_id, domain="[('category_id', '=', product_uom_category_id)]")
    
    unit_amount = fields.Float(required=False, string= 'Unit Price', compute='_compute_from_product_id_company_id', store=True, readonly=True, digits='Account')
    
    quantity = fields.Float(required=False, readonly=True, digits='Product Unit of Measure', default=1)
    tax_ids = fields.Many2many('account.tax', 'expense_tax', 'expense_id', 'tax_id', compute='_compute_from_product_id_company_id', store=True, readonly=True,domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]", string='Taxes')
    
    
    
    expense_line = fields.One2many('hr.expense.line', 'expense_id', string='Expense Lines', copy=True)
    payment_mode = fields.Selection([
        ("own_account", "Employee (to reimburse)"),
        ("company_account", "Expense to Vendor")
    ], default='own_account', tracking=True, states={'done': [('readonly', True)], 'approved': [('readonly', True)], 'reported': [('readonly', True)]}, string="Paid By")
    previous_balance = fields.Float("Previous Balance", store=False, compute='_compute_advance', digits='Account')
    advance_amount = fields.Float("Budget Amount", store=False, compute='_compute_advance', digits='Account')
    used_amount = fields.Float("Total Expensed", store=False, compute='_compute_advance', digits='Account')
    balance_amount = fields.Float("Balance Amount", store=False, compute='_compute_advance', digits='Account')


    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', tracking=True)
    amount_tax = fields.Monetary(string='Total Taxes', store=True, readonly=True, compute='_amount_all')
    amount_total = fields.Monetary(string='Total Amount', store=True, readonly=True, compute='_amount_all')    
    

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
    
    
    expense_id = fields.Many2one('hr.expense', index=True, required=True, ondelete='cascade')
    
    sequence = fields.Integer(string='Sequence', default=10)
    partner_id = fields.Many2one(
        'res.partner', 'Name', help='Enter here any kind of contact indivisual/company.',
        groups="hr.group_hr_user", store=True)
    
    name = fields.Char('Note', store=True)
    
    currency_id = fields.Many2one(related='expense_id.currency_id', store=True, string='Currency', readonly=True)
    #amount = fields.Monetary(string='Amount', store=True, digits='Account')
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])

    price_unit = fields.Float(string='Amount', required=True, digits='Account')
   
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', store=True, digits='Account')
    price_total = fields.Monetary(compute='_compute_amount', string='Total', store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Tax', store=True)    
    state = fields.Selection(related='expense_id.state', store=True, readonly=False)
    
    company_id = fields.Many2one('res.company', related='expense_id.company_id', string='Company', store=True, readonly=True)
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")
    
    @api.depends('price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            vals = line._prepare_compute_all_values()
            taxes = line.taxes_id.compute_all(
                vals['price_unit'],
                vals['currency_id'],
                vals['qty'])
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    def _prepare_compute_all_values(self):
        self.ensure_one()
        return {
            'price_unit': self.price_unit,
            'currency_id': self.expense_id.currency_id,
            'qty': 1,
            #'partner': self.partner_id,
        }