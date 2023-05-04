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
    
    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, default='SA', tracking=True)
    salary_month = fields.Date('Salary Month', store=True, default=date.today().strftime('%Y-%m-01'), tracking=True)
    adjustment_line = fields.One2many('salary.adjustment.line', 'adjustment_id', string='Adjustment Lines', store=True, tracking=True)
    adjust_type = fields.Selection([('sal', "Salary"),('bonus', "Bonus"),('fnf', "Full & Final")], string="Adjustment Type", default='sal', required=True, tracking=True)
    note = fields.Char('Notes', store=True, index=True, tracking=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'SA') == 'SA':
            vals['name'] = self.env['ir.sequence'].next_by_code('adjustment.code')
        return super(SalaryAdjustment, self).create(vals)
    
    def unlink(self):
        for line in self:
            if line.id:
                raise UserError(_('Cannot delete a Adjustment which is Entry Done'))
        return super(SalaryAdjustment, self).unlink()      


class SalaryAdjustmentLine(models.Model):
    _name = 'salary.adjustment.line'
    _description = 'Salary Adjustment Line'
    
    sequence = fields.Integer(string='Sequence', default=10)
    adjustment_id = fields.Many2one('salary.adjustment', string='Adjustment Reference', index=True, required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    emp_id = fields.Char(related = 'employee_id.emp_id', string="Emp ID", readonly=True, store=True)
    mode_type = fields.Selection([('Pay', "Pay"),('Deduct', "Deduct")], string="Mode Type", default='Deduct', required=True)
    adjustment_type = fields.Many2one('hr.payslip.input.type', string='Type',required=True,store=True)
    amount = fields.Float(string='Amount', store=True)
    
    @api.onchange('mode_type')
    def onchange_partner_id(self):
        self.adjustment_type = ''
        for rec in self:
            if rec.mode_type == 'Pay':
                return {'domain':{'adjustment_type': [('is_deduction','=',False)]}}
            if rec.mode_type == 'Deduct':
                return {'domain':{'adjustment_type': [('is_deduction','=',True)]}}    
    
    @api.constrains('mode_type', 'adjustment_type')
    def _check_adjustment_type(self):
        for line in self:
            if line.mode_type and line.adjustment_type and line.mode_type == 'Deduct' and line.adjustment_type.is_deduction == False:
                raise ValidationError(_('Invalid selection: deduction adjustment type should be selected for deduction mode type.'))
            if line.mode_type and line.adjustment_type and line.mode_type == 'Pay' and line.adjustment_type.is_deduction == True:
                raise ValidationError(_('Invalid selection: payment adjustment type should be selected for payment mode type.'))
    
   
    def write(self, values):
        if 'employee_id' in values:
            for line in self:
                employee = self.env['hr.employee'].browse(values['employee_id']).name_get()[0][1]
                line.adjustment_id.message_post_with_view('taps_hr.track_salary_adjustment_line_template_employee',
                                                     values={'line': line, 'employee_id': employee},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'mode_type' in values:
            for line in self:
                mode_type_name = dict(self.env['salary.adjustment.line'].fields_get('mode_type')['mode_type']['selection'])[values['mode_type']]
                line.adjustment_id.message_post_with_view('taps_hr.track_salary_adjustment_line_template_employee',
                                                     values={'line': line, 'mode_type': mode_type_name},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'adjustment_type' in values:
            for line in self:
                type = self.env['hr.payslip.input.type'].browse(values['adjustment_type']).name_get()[0][1]
                line.adjustment_id.message_post_with_view('taps_hr.track_salary_adjustment_line_template_employee',
                                                     values={'line': line, 'adjustment_type': type},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'amount' in values:
            for line in self:
                # if line.acvd_id.state != 'draft':
                line.adjustment_id.message_post_with_view('taps_hr.track_salary_adjustment_line_template_employee',
                                                     values={'line': line, 'amount': values['amount']},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        return super(SalaryAdjustmentLine, self).write(values)
    
    def unlink(self):
        for line in self:
            if line.id:
                raise UserError(_('Cannot delete a Objective line which is Entry Done'))
        return super(SalaryAdjustmentLine, self).unlink()  
