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

    name = fields.Char(string="Name", default="/", readonly=True, help="Name of the Retention Bonus Scheme")
    date = fields.Date(string="Date", default=fields.Date.today(), readonly=True, help="Date")
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True, help="Employee")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", readonly=True, store=True,
                                    string="Department", help="Employee")
    installment = fields.Integer(string="No Of Installments", default=1, help="Number of installments")
    payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today(), help="Date of "
                                                                                                             "the "
                                                                                                             "paymemt")
    bonus_lines = fields.One2many('hr.retention.bonus.line', 'bonus_id', string="Bonus Line", index=True)
    company_id = fields.Many2one('res.company', 'Company', related="employee_id.company_id", store=True, readonly=True, help="Company",
                                 states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency', required=True, help="Currency",
                                  default=lambda self: self.env.user.company_id.currency_id)
    job_position = fields.Many2one('hr.job', related="employee_id.job_id", store=True, readonly=True, string="Job Position",
                                   help="Job position")
    bonus_amount = fields.Float(string="Bonus Amount", required=True, help="Bonus amount")
    total_amount = fields.Float(string="Total Amount", store=True, readonly=True, compute='_compute_retention_bonus_amount',
                                help="Total Retention Bonus Scheme amount")
    balance_amount = fields.Float(string="Balance Amount", store=True, compute='_compute_retention_bonus_amount', help="Balance amount")
    total_paid_amount = fields.Float(string="Total Paid Amount", store=True, compute='_compute_retention_bonus_amount',
                                     help="Total paid amount")
    criteria = fields.Selection([
        ('Appointment Terms', 'Appointment Terms'),
        ('As per Policy', 'As per Policy'),
        ('Special Retention Bonus', 'Special Retention Bonus'),
    ], string="Criteria", tracking=True, copy=False, )    

    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approval_1', 'Submitted'),
        ('approve', 'Approved'),
        ('refuse', 'Refused'),
        ('cancel', 'Canceled'),
    ], string="State", default='draft', tracking=True, copy=False, )

    @api.model
    def create(self, values):
        loan_count = self.env['hr.retention.bonus'].search_count(
            [('employee_id', '=', values['employee_id']), ('state', '=', 'approve'),
             ('balance_amount', '!=', 0)])
        if loan_count:
            raise ValidationError(_("The employee has already a pending installment"))
        else:
            retention_date = values.get('date')
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

    # def unlink(self):
    #     for bonus in self:
    #         if bonus.state not in ('draft', 'cancel'):
    #             raise UserError(
    #                 'You cannot delete a Retention Bonus Scheme which is not in draft or cancelled state')
    #     return super(HrRetentionBonus, self).unlink()


class InstallmentLine(models.Model):
    _name = "hr.retention.bonus.line"
    _description = "Installment Line"

    date = fields.Date(string="Payment Date", required=True, help="Date of the payment")
    employee_id = fields.Many2one('hr.employee', string="Employee", help="Employee")
    amount = fields.Float(string="Amount", required=True, help="Amount")
    paid = fields.Boolean(string="Paid", help="Paid")
    bonus_id = fields.Many2one('hr.retention.bonus', string="Retention Bonus Ref.", help="Retention Bonus Scheme")
    adjustment_type = fields.Many2one('hr.payslip.input.type', string='Type',required=True,store=True, domain="[('code', '=', 'INCENTIVE')]", default=44)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _compute_retention_bonus_scheme(self):
        """This compute the bonus amount and total retention scheme count of an employee.
            """
        self.retention_bonus_scheme_count = self.env['hr.retention.bonus'].search_count([('employee_id', '=', self.id)])

    retention_bonus_scheme_count = fields.Integer(string="Retention Bonus Scheme Count", compute='_compute_retention_bonus_scheme')

