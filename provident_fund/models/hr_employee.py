# -*- coding: utf-8 -*-

from odoo import fields, models
from odoo.exceptions import UserError

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    providient_pay_line_ids = fields.One2many('hr.payslip.line', 'employee_id', string='', domain=[('salary_rule_id.is_providient_found', '=', 'True'), ('slip_id.state', '=', 'done')])
    contribution_sum = fields.Float("Provident Fund Contribution", store=True, copy=True)
    
    

    # def _compute_contribution_sum(self):
    #     # raise UserError(('ssss'))
    #     for rec in self:
    #         odoo_pf = abs(sum(rec.providient_pay_line_ids.mapped('total')))
    #         tms_pf_record = self.env['provident.fund.line'].search([('employee_id', '=', rec.id)])
    #         tms_pf = 0
    #         if tms_pf_record:
    #             tms_pf = abs(sum(tms_pf_record.mapped('pf_amount')))
    #         rec.contribution_sum = odoo_pf+tms_pf
        
