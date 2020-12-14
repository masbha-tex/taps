# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


# class HrPayrollStructureType(models.Model):
#     _inherit = 'hr.payroll.structure.type'
#     _description = "Payroll Structure Type"

#     work_entry_generation = fields.Selection([('attendance', 'Attendance')])

#     @api.onchange('work_entry_generation')
#     def _onchange_work_entry_generation(self):
#         if self.work_entry_generation == 'attendance':
#             calendar = self.env.ref('resource_calendar_7d_24h', raise_if_not_found=False)
#             if calendar:
#                 self.default_resource_calendar_id = calendar
