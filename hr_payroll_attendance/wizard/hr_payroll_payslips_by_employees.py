# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'

    def _check_undefined_slots(self, work_entries, payslip_run):
        """ For payslips generated based on employee attendance, we don't care
        about undefined slots in the resource calendar.
        """
        # work_entries = work_entries.filtered(lambda w: w.contract_id.structure_type_id.work_entry_generation != 'attendance')
        return super()._check_undefined_slots(self.env['hr.work.entry'], payslip_run)
