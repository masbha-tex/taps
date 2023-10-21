# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError, UserError


class HrRetentionBonus(models.Model):
    _name = 'hr.retention.bonus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Retention Bonus Scheme"

    @api.model
    def default_get(self, field_list):
        result = super(HrRetentionBonus, self).default_get(field_list)
        if result.get('user_id'):
            ts_user_id = result['user_id']
        else:
            ts_user_id = self.env.context.get('user_id', self.env.user.id)
        result['employee_id'] = self.env['hr.employee'].search([('user_id', '=', ts_user_id)], limit=1).id
        
        # result['date'] = self.env['hr.employee'].search([('id', '=', result.get('user_id'))], limit=1).joining_date
        return result

    def _compute_retention_bonus_amount(self):
        total_paid = 0.0
        for bonus in self:
            for line in bonus.bonus_lines:
                if line.paid:
                    total_paid += line.amount
            balance_amount = bonus.bonus_amount - total_paid
            bonus.total_amount = bonus.bonus_amount
            bonus.balance_amount = balance_amount
            bonus.total_paid_amount = total_paid

    @api.depends('employee_id')
    def _compute_default_date(self):
        if self.employee_id:
            self.date = self.employee_id.joining_date
        else:
            fields.Date.today()
      
         

    name = fields.Char(string="Number", readonly=True, help="Name of the Retention Bonus Scheme")
    employee_id = fields.Many2one('hr.employee', string="Employee", tracking=True, required=True, help="Employee")    
    date = fields.Date(string="Effective Date ", compute=_compute_default_date, store=True, required=True, readonly=False,  tracking=True, help="Effective Date") 
    duration = fields.Integer(default=1, string="Duration in Month", required=True, tracking=True, help="Duration in Month")
    

    
    @api.depends('date', 'duration')
    def _get_default_entitlement_date(self):
        for record in self:
            if record.date and record.duration:
                record.entitlement_date = record.date + relativedelta(months=record.duration)
                # record.payment_date = record.date + relativedelta(months=record.duration)
            else:
                record.entitlement_date = fields.Date.today()
                # record.payment_date = fields.Date.today()

    @api.depends('instant_payment')
    def _get_default_installment_date(self):
        for record in self:
            if record.instant_payment == '3':
                record.installment = 3
            elif record.instant_payment == '6':
                record.installment = 6
            elif record.instant_payment == '12':
                record.installment = 12
            else:
                record.installment = 1  

        
    entitlement_date = fields.Date(string="Entitlement Date", compute=_get_default_entitlement_date, store=True, required=True, readonly=False, help="Date of the Entitlement")   

    department_id = fields.Many2one('hr.department', related="employee_id.department_id", tracking=True, readonly=True, store=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", compute=_get_default_installment_date, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, tracking=True, default=fields.Date.today(), help="Date of the paymemt")
    bonus_lines = fields.One2many('hr.retention.bonus.line', 'bonus_id', string="Bonus Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id", store=True, readonly=True, help="Company",
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', tracking=True, required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id.browse(55))
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", store=True, readonly=True, string="Job Position",
                                   help="Job position")
    bonus_amount = fields.Float(string="Bonus Amount",  tracking=True, required=True, help="Bonus amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_retention_bonus_amount',
                                help="Total Retention Bonus Scheme amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_retention_bonus_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", tracking=True, store=True, compute='_compute_retention_bonus_amount',
                                     help="Total paid amount")
    criteria = fields.Selection([
        ('Appointment Terms', 'Appointment Terms'),
        ('Special Retention Bonus', 'Special Retention Bonus'),
        ('GET policy', 'GET policy'),
        ('DET Policy', 'DET Policy'),
        ('ST policy', 'ST policy'),
        ('KMP policy', 'KMP policy'),
    ], string="Criteria", default='Appointment Terms', tracking=True, copy=True, required=True, readonly=False, store=True)
    instant_payment = fields.Selection([
        ('3', 'Payment by next 3 months'),
        ('6', 'Payment by next 6 months'),
        ('12', 'Payment by next 12 months'),
    ], string="Instant Payment", tracking=True, copy=True, store=True)        

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, store=True, required=True)



        
    @api.model
    def create(self, values):
        loan_count = self.env['hr.retention.bonus'].sudo().search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            retention_date = values.get('entitlement_date')
            values['name'] = self.env['ir.sequence'].next_by_code('hr.retention.bonus.seq', sequence_date=retention_date)
            res = super(HrRetentionBonus, self).create(values)
            return res
            
    def compute_installment(self):
        """This automatically create the installment the employee need to pay to
        company based on payment start date and the no of installments.
            """
        for bonus in self:
            bonus.bonus_lines.unlink()
            date_start = datetime.strptime(str(bonus.payment_date), '%Y-%m-%d')
            amount = bonus.bonus_amount / bonus.installment
            for i in range(1, bonus.installment + 1):
                self.env['hr.retention.bonus.line'].create({
                    'date': date_start,
                    'amount': amount,
                    'employee_id': bonus.employee_id.id,
                    'bonus_id': bonus.id})
                date_start = date_start + relativedelta(months=1)
            bonus._compute_retention_bonus_amount()
        return True
        
    def action_draft(self):
        return self.write({'state': 'draft'})
        
    def action_refuse(self):
        return self.write({'state': 'refuse'})

    def action_submit(self):
        self.write({'state': 'waiting_approval_1'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    def action_approve(self):
        for data in self:
            if not data.bonus_lines:
                raise ValidationError(_("Please Compute installment"))
            else:
                self.write({'state': 'approve'})

                

    def unlink(self):
        for bonus in self:
            if bonus.state == 'draft':
                raise UserError(
                    'Once saved, You cannot delete a Retention Bonus Scheme.')
        return super(HrRetentionBonus, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.retention.bonus.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    bonus_id = fields.Many2one('hr.retention.bonus', string="Retention Bonus Ref.", help="Retention Bonus Scheme")
    # adjustment_type = fields.Many2one('hr.payslip.input.type', string='Type',required=True,store=True, domain="[('code', '=', 'INCENTIVE')]", default=44)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_retention_bonus_scheme(self):
        """This compute the bonus amount and total retention scheme count of an employee.
            """
        self.retention_bonus_scheme_count = self.env['hr.retention.bonus'].sudo().search_count([('employee_id', '=', self.id)])

    retention_bonus_scheme_count = fields.Integer(string="Retention Bonus Scheme Count", compute='_compute_retention_bonus_scheme', groups="hr_retention_bonus.group_manager_retention_bonus,hr_retention_bonus.group_user_retention_bonus")
