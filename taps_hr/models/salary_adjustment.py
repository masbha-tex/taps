import base64

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval


class SalaryAdjustment(models.Model):
    _name = 'salary.adjustment'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Salary Adjustment'
    
    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, default='SA')
    salary_month = fields.Date('Salary Month', store=True, default=date.today().strftime('%Y-%m-01'))
    adjustment_line = fields.One2many('salary.adjustment.line', 'adjustment_id', string='Adjustment Lines', store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'SA') == 'SA':
            vals['name'] = self.env['ir.sequence'].next_by_code('adjustment.code')
        return super(SalaryAdjustment, self).create(vals) 


class SalaryAdjustmentLine(models.Model):
    _name = 'salary.adjustment.line'
    _description = 'Salary Adjustment Line'
    
    
    @api.onchange('mode_type')
    def onchange_partner_id(self):
        self.adjustment_type = ''
        for rec in self:
            if rec.mode_type == 'False':
                return {'domain':{'adjustment_type': [('is_deduction','=',False)]}}
            if rec.mode_type == 'True':
                return {'domain':{'adjustment_type': [('is_deduction','=',True)]}}
    
    
    adjustment_id = fields.Many2one('salary.adjustment', string='Adjustment Reference', index=True, required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    emp_id = fields.Char(related = 'employee_id.emp_id', string="Emp ID", readonly=True, store=True)
    mode_type = fields.Selection([('False', "Pay"),('True', "Deduct")], string="Mode Type", required=True)
    adjustment_type = fields.Many2one('hr.payslip.input.type', string='Type',store=True)
    amount = fields.Float(string='Amount', store=True)