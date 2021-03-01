# -*- coding:utf-8 -*-

from odoo import models


class HrWorkEntryRegenerationWizard(models.TransientModel):
    _inherit = 'hr.work.entry.regeneration.wizard'

    def attendance_regenerate_work_entries(self):
        action = self.regenerate_work_entries()

        attendances = self.env['hr.attendance'].search([('employee_id', '=', self.employee_id.id),
                                                        ('check_out', '>=', self.date_from),
                                                        ('check_in', '<=', self.date_to)])
        attendances._update_work_entries()
        return action
