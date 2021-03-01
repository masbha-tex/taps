# -*- coding: utf-8 -*-

from odoo import fields, models

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    providient_pay_line_ids = fields.One2many('hr.payslip.line', 'employee_id', string='', domain=[('salary_rule_id.is_providient_found', '=', 'True'), ('slip_id.state', '=', 'done')])
    contribution_sum = fields.Float("Provident Fund Contribution", compute='_compute_contribution_sum')

    def _compute_contribution_sum(self):
        self.contribution_sum = abs(sum(self.providient_pay_line_ids.mapped('total')))
