# -*- coding:utf-8 -*-

import pytz

from odoo import api, fields, models


class Attendance(models.Model):
    _inherit = 'hr.attendance'

    @api.model_create_multi
    def create(self, vals_list):
        attendances = super().create(vals_list)
        attendances.filtered('check_out').sudo()._update_work_entries()
        return attendances

    def _update_work_entries(self):
        for attendance in self.filtered('employee_id'):
            overtimes = self.env['hr.overtime'].search([('employee_id', '=', attendance.employee_id.id),
                                                        ('end_date', '>=', attendance.check_in),
                                                        ('start_date', '<=', attendance.check_out)])
            overtimes._create_work_entries()

            work_entries = self.env['hr.work.entry'].search([('employee_id', '=', attendance.employee_id.id),
                                                            ('date_stop', '>=', attendance.check_in),
                                                            ('date_start', '<=', attendance.check_out)], order='date_start')
            if work_entries:
                if not work_entries[0].overtime_id.extra_overtime_behaviour == 'ignore' or work_entries[0].date_start < attendance.check_in:
                    work_entries[0].date_start = attendance.check_in
                if not work_entries[-1].overtime_id.extra_overtime_behaviour == 'ignore' or work_entries[-1].date_stop > attendance.check_out:
                    work_entries[-1].date_stop = attendance.check_out

    def write(self, vals):
        # if we change the checkout or checkin date and the entries have already been modified for that period (check_out is set)
        # archive them like in regenerate_work_entries method
        check_in = fields.Datetime.from_string(vals.get('check_in'))
        check_out = fields.Datetime.from_string(vals.get('check_out'))
        if (self.check_out and check_out) or check_in or vals.get('employee_id'):
            date_from = min([check_in, self.check_in]) if check_in else self.check_in
            date_to = max([check_out, self.check_out])
            self._regenerate_work_entries(date_from, date_to)
            res = super().write(vals)
            if vals.get('employee_id'):
                self._regenerate_work_entries(date_from, date_to)
        else:
            res = super().write(vals)
        self.sudo()._update_work_entries()
        return res

    def unlink(self):
        self.filtered('check_out').sudo()._regenerate_work_entries(self.check_in, self.check_out)
        res = super().unlink()
        return res

    def _regenerate_work_entries(self, date_from, date_to):
        if not date_from or not date_to:
            return
        tz = pytz.timezone(self.employee_id.tz or 'UTC')
        date_to = tz.normalize(pytz.utc.localize(date_to))
        date_from = tz.normalize(pytz.utc.localize(date_from))
        self.env['hr.work.entry.regeneration.wizard'].create({
            'employee_id': self.employee_id.id,
            'date_from': date_from,
            'date_to': date_to,
        }).sudo().regenerate_work_entries()
