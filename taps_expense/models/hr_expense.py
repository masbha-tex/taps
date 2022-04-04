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
    
    @api.depends('sheet_id', 'sheet_id.account_move_id', 'sheet_id.state')
    def _compute_state(self):
        for expense in self:
            if not expense.sheet_id or expense.sheet_id.state == 'draft':
                expense.state = "draft"
            elif expense.sheet_id.state == "checked":
                expense.state = "checked"
            elif expense.sheet_id.state == "cancel":
                expense.state = "refused"
            elif expense.sheet_id.state == "approve" or expense.sheet_id.state == "post":
                expense.state = "approved"
            elif not expense.sheet_id.account_move_id:
                expense.state = "reported"
            else:
                expense.state = "done"

                
    @api.model
    def _get_employee_id_domain(self):
        res = [('id', '=', 0)] # Nothing accepted by domain, by default
        if self.user_has_groups('hr_expense.group_hr_expense_user') or self.user_has_groups('account.group_account_user'):
            res = "['|', ('company_id', '=', False)]"  # Then, domain accepts everything
        elif self.user_has_groups('hr_expense.group_hr_expense_team_approver') and self.env.user.employee_ids:
            user = self.env.user
            employee = self.env.user.employee_id
            res = [
                '|', '|', '|',
                ('department_id.manager_id', '=', employee.id),
                ('parent_id', '=', employee.id),
                ('id', '=', employee.id),
                ('expense_manager_id', '=', user.id),
            ]
        elif self.env.user.employee_id:
            employee = self.env.user.employee_id
            res = [('id', '=', employee.id)]
        return res                
                
    #name = fields.Char('Code', store=True, readonly=True, default='New')#default=_('New')  
    
    name = fields.Char('Expense Reference', required=True,  readonly=True, index=True, copy=False, default='New')
    
    employee_id = fields.Many2one('hr.employee', string="Billing Ref.",
        store=True, required=True, readonly=False, tracking=True,
        states={'approved': [('readonly', True)], 'done': [('readonly', True)]}, check_company=False, domain=False)  
    
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
    
    state = fields.Selection(selection_add=[('checked', 'Checked'),('approved',)])
#     state = fields.Selection([
#         ('draft', 'To Submit'),
#         ('reported', 'Submitted'),
#         ('checked', 'Checked'),
#         ('approved', 'Approved'),
#         ('done', 'Paid'),
#         ('refused', 'Refused')
#     ], compute='_compute_state', string='Status', copy=False, index=True, readonly=True, store=True, default='draft', help="Status of the expense.")    

    def float_to_time(self,hours):
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(round(60 * fractional, precision_digits=0)), 0)    
    
#     def unlink(self):
#         for expense in self:
#             if expense.state in ['done', 'approved']:
#                 raise UserError(_('You cannot delete a posted or approved expense.'))
#         return super(HrExpense, self).unlink()
    
    def action_view_sheet(self):
        #self.env["hr.expense.sheet"].search([('id','=',self.sheet_id.id)]).unlink()
        if self.sheet_id.state != 'approve':
            self.env['hr.expense.sheet'].search([('id','=',self.sheet_id.id)]).write({'expense_lines':[(6, 0, '')]})
            self.env['hr.expense.sheet'].search([('id','=',self.sheet_id.id)]).write({'expense_lines':[(6, 0, self.expense_line.ids)]})
        #sheet = self._create_sheet_from_expenses()
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': self.sheet_id.id
        }

    def action_submit_expenses(self):
        sheet = self._create_sheet_from_expenses()
        return {
            'name': _('New Expense Report'),
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.expense.sheet',
            'target': 'current',
            'res_id': sheet.id,
        }

    def _create_sheet_from_expenses(self):
        if any(expense.state != 'draft' or expense.sheet_id for expense in self):
            raise UserError(_("You cannot report twice the same line!"))
        if len(self.mapped('employee_id')) != 1:
            raise UserError(_("You cannot report expenses for different employees in the same report."))
        if any(not expense.product_id for expense in self):
            raise UserError(_("You can not create report without product."))

        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': self.company_id.id,
            'employee_id': self[0].employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'expense_line_ids': [(6, 0, todo.ids)],
            'expense_lines': [(6, 0, todo.expense_line.ids)]
        })
        return sheet
    
    def _create_sheet_from_expenses(self):
        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].create({
            'company_id': self.company_id.id,
            'employee_id': self[0].employee_id.id,
            'name': todo[0].name if len(todo) == 1 else '',
            'expense_lines': [(6, 0, todo.expense_line.ids)]
        })
        return sheet    
    

    def _update_sheet_from_expenses(self):
        todo = self.filtered(lambda x: x.payment_mode=='own_account') or self.filtered(lambda x: x.payment_mode=='company_account')
        sheet = self.env['hr.expense.sheet'].write({
            'expense_lines': [(6, 0, '')]
        })
        return sheet    
    
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
            
            pre_advance = self.env['hr.imprest'].search([('imprest_employee', '=', self.employee_id.id), ('imprest_date', '>=', pr_fromdate), ('imprest_date', '<=', pr_todate), ('state', '=', 'approved')])
            
            cr_advance = self.env['hr.imprest'].search([('imprest_employee', '=', self.employee_id.id), ('imprest_date', '>=', cu_fromdate), ('imprest_date', '<=', cu_todate), ('state', '=', 'approved')])
            
            
            
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
    
    
class taps_expense_sheet(models.Model):
    _inherit = 'hr.expense.sheet'
    
    #state = fields.Selection(selection_add=[('checked', 'Checked')], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True, help='Expense Report State')
    product_id = fields.Many2one(related='expense_line_ids.product_id', string='Product', store=False, readonly=True)
    ex_currency_id = fields.Many2one(related='expense_line_ids.currency_id', store=True, string='Expense Currency', readonly=True)
    total_actual_amount = fields.Monetary('Total Actual Amount', compute='_compute_actual_amount', store=True, tracking=True, currency_field='ex_currency_id')
    
    state = fields.Selection(selection_add=[('checked', 'Checked'),('approve',)], ondelete={'checked': lambda records: record.write({'state': 'draft'})})
    
    expense_lines = fields.Many2many('hr.expense.line', string='Expense Lines', copy=False, domain="[('id', '=', expense_line_ids)]")
    

    amount_untaxed = fields.Monetary(related='expense_line_ids.amount_untaxed', string='Untaxed Amount', readonly=True, tracking=True, currency_field='ex_currency_id')
    amount_tax = fields.Monetary(related='expense_line_ids.amount_tax', string='Total Taxes', readonly=True, currency_field='ex_currency_id')#, compute='_amount_all'
    amount_total = fields.Monetary(related='expense_line_ids.amount_total', string='Total Amount', readonly=True, currency_field='ex_currency_id')
    
    purpose = fields.Char('Description', related='expense_line_ids.purpose', store=True, readonly=True)
    
    #employee_id = fields.Many2one('hr.employee', string="Employee", required=True, readonly=True, domain=False)
    
    employee_id = fields.Many2one('hr.employee', string="Employee",
        store=True, required=True, readonly=False, tracking=True, check_company=False, domain=False)      
#     state = fields.Selection([
#         ('draft', 'Draft'),
#         ('submit', 'Submitted'),
#         ('checked', 'Checked'),
#         ('approve', 'Approved'),
#         ('post', 'Posted'),
#         ('done', 'Paid'),
#         ('cancel', 'Refused')
        
#     ], string='Status', index=True, readonly=True, tracking=True, copy=False, default='draft', required=True, help='Expense Report State')

    
    @api.depends('expense_line_ids.total_amount')
    def _compute_actual_amount(self):
        for sheet in self:
            sheet.total_actual_amount = sum(sheet.expense_line_ids.mapped('total_amount'))    
    
    def action_submit_sheet(self):
        self.write({'state': 'submit'})
        #self.activity_update()    
    
    def action_check_sheet(self):
        self.write({'state': 'checked'})
        self.activity_update()
        
        
    def activity_update(self):
        for expense_report in self.filtered(lambda hol: hol.state == 'checked'):
            self.activity_schedule(
                'hr_expense.mail_act_expense_approval',
                user_id=expense_report.sudo()._get_responsible_for_approval().id or self.env.user.id)
        self.filtered(lambda hol: hol.state == 'approve').activity_feedback(['hr_expense.mail_act_expense_approval'])
        self.filtered(lambda hol: hol.state in ('draft', 'cancel')).activity_unlink(['hr_expense.mail_act_expense_approval'])        
        
        

    def approve_expense_sheets(self):
        if not self.user_has_groups('hr_expense.group_hr_expense_team_approver'):
            raise UserError(_("Only Managers and HR Officers can approve expenses"))
        elif not self.user_has_groups('hr_expense.group_hr_expense_manager'):
            current_managers = self.employee_id.expense_manager_id | self.employee_id.parent_id.user_id | self.employee_id.department_id.manager_id.user_id

            if self.employee_id.user_id == self.env.user:
                raise UserError(_("You cannot approve your own expenses"))

            if not self.env.user in current_managers and not self.user_has_groups('hr_expense.group_hr_expense_user') and self.employee_id.expense_manager_id != self.env.user:
                raise UserError(_("You can only approve your department expenses"))
        
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('There are no expense reports to approve.'),
                'type': 'warning',
                'sticky': False,  #True/False will display for few seconds if false
            },
        }
        filtered_sheet = self.filtered(lambda s: s.state in ['checked', 'draft'])
        if not filtered_sheet:
            return notification
        for sheet in filtered_sheet:
            sheet.write({'state': 'approve', 'user_id': sheet.user_id.id or self.env.user.id})
        notification['params'].update({
            'title': _('The expense reports were successfully approved.'),
            'type': 'success',
            'next': {'type': 'ir.actions.act_window_close'},
        })
            
        self.activity_update()
        return notification        
    