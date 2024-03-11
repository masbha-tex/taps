# -*- coding: utf-8 -*-

import time
import babel
from odoo.exceptions import UserError,ValidationError
from odoo import models, fields, api, tools, _
from datetime import datetime


# class HrPayslipInput(models.Model):
#     _inherit = 'hr.payslip.input'

    # retention_line_id = fields.Many2one('hr.retention.bonus.line', string="Retention Installment", help="Retention installment")


# class HrPayslipsss(models.Model):
#     _inherit = 'hr.payslip'


    # @api.onchange('struct_id', 'date_from', 'date_to', 'employee_id')
    # def onchange_employee_retention_bonus(self):
    #     for data in self:
    #         print("Data:", data)
    #         if (not data.employee_id) or (not data.date_from) or (not data.date_to):
    #             return
    #         if data.input_line_ids.input_type_id:
    #             data.input_line_ids = [(5, 0, 0)]
    #         print("Employee:", data)
    #         bonus_line = data.struct_id.input_line_type_ids.filtered(
    #             lambda x: x.code == 'OTHERSALW')
    #         print("Data2213:")
    #         # loan_line = self.env.ref('ent_ohrms_loan.hr_rule_input_loan')
    #         if bonus_line:
    #             get_amount = self.env['hr.retention.bonus'].search([
    #                 ('employee_id', '=', data.employee_id.id),
    #                 ('state', '=', 'draft')
    #             ], limit=1)
    #             print(get_amount,'get_amount')

    #             if get_amount:
    #                 for lines in get_amount:
    #                     for line in lines.bonus_lines:
    #                         if data.date_from <= line.date <= data.date_to:
    #                             if not line.paid:
    #                                 amount = line.amount
    #                                 name = bonus_line.id
    #                                 # loan_line.input_id.struct_id = data.struct_id
    #                                 bonus = line.id
    #                                 self.input_data_line(name, amount, bonus)

    # def action_payslip_done(self):
    #     for line in self.input_line_ids:
    #         if line.retention_line_id:
    #             line.retention_line_id.paid = True
    #             line.retention_line_id.bonus_id._compute_retention_bonus_amount()
    #     return super(HrPayslip, self).action_payslip_done()

    # def input_data_line(self, name, amount, bonus):
    #     for data in self:
    #         check_lines = []
    #         new_name = self.env['hr.payslip.input.type'].search([
    #             ('id', '=', name)])
    #         line = (0, 0, {
    #             'input_type_id': new_name,
    #             'amount': amount,
    #             'name': 'OTHERSALW',
    #             'retention_line_id': bonus
    #         })
    #         check_lines.append(line)
    #         data.input_line_ids = check_lines

    # def action_refresh_from_work_entries(self):
    #     # Refresh the whole payslip in case the HR has modified some work entries
    #     # after the payslip generation
    #     self.ensure_one()
    #     self.onchange_employee_retention_bonus()
    #     self.compute_sheet()    




