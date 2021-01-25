# -*- coding: utf-8 -*-

from odoo import models, fields, api


class HrOvertime(models.Model):
    _name = 'hr.overtime'

    employee_id = fields.Many2one('hr.employee', string="Employee")
    start_date = fields.Datetime("Start Time")
    end_date = fields.Datetime("End Time")
    number_of_hours = fields.Float("Number Of Hours", compute='_compute_number_of_hours')

    def _compute_number_of_hours(self):
        if self.end_date and self.start_date:
            self.number_of_hours = (self.end_date - self.start_date).total_seconds() / 3600
        else:
            self.number_of_hours = False
