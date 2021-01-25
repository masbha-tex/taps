# -*- coding: utf-8 -*-

import datetime

from odoo import models, fields

class Hr_employee_inherit_(models.Model):
    _inherit = 'hr.employee'

    def get_overtime(self, date_start, date_stop):

        hr_overtime_ids = self.env['hr.overtime'].search([
            ('employee_id', '=', self.id),
            ('start_date', '>=', date_start),
            ('end_date', '<=', date_stop)
        ])

        return sum([ot.number_of_hours for ot in hr_overtime_ids])

    # def generate_work_entries(self, date_start, date_stop):
    #     res = super().generate_work_entries(date_start, date_stop)
    #     date_start = fields.Date.to_date(date_start)
    #     date_stop = fields.Date.to_date(date_stop)

    #     vals_list = []

    #     work_entry_overtime_type_id = self.env.ref('work_entry_type_overtime').id
    #     hr_overtime_ids = self.env['hr.overtime'].search([
    #         ('employee_id', '=', self.id),
    #         ('start_date', '>=', date_start),
    #         ('end_date', '<=', date_stop),
    #     ])
    #     existing_work_entries = self.env['hr.work.entry'].search([
    #         ('date_start', '>=', date_start),
    #         ('date_stop', '<=', date_stop),
    #         ('work_entry_type_id', '=', work_entry_overtime_type_id.id),
    #     ])

    #     for hr_overtime_id in hr_overtime_ids:
    #          self.env['hr.work.entry'].search([
    #         ('date_start', '>=', date_start),
    #         ('date_stop', '<=', date_stop),
    #         ('work_entry_type_id', '=', work_entry_overtime_type_id.id),
    #     ])

    #     hr_attendance_ids = self.env['hr.attendance'].search([
    #         ('employee_id', '=', self.id),
    #         ('check_in', '>=', date_start),
    #         ('check_out', '<=', date_stop),
    #     ])

    #     work_entry_type_id = self.env.ref('hr_work_entry.work_entry_type_attendance').id
    #     for hr_attendance_id in hr_attendance_ids:
    #         vals_list.append({
    #             'name': "%s: %s" % (work_entry_type_id.name, self.name),
    #             'date_start': hr_attendance_id.check_in,
    #             'date_stop': hr_attendance_id.check_out,
    #             'work_entry_type_id': work_entry_type_id.id,
    #             'employee_id': self.id,
    #             'company_id': self.company_id.id,
    #             'state': 'draft',
    #         })

    #     return res and bool(self.env['hr.work.entry'].create(vals_list))
