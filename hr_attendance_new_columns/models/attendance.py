#-*- coding: utf-8 -*-

from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
#     _description = 'hr_attendance_new_columns.hr_attendance_new_columns'

    date = fields.date(string = "Date", store=True)
    inTime = fields.float(string = "In-Time")
    inFlag = fields.char("In-Flag")
    outTime = fields.float(string = "Out-Time")
    outFlag = fields.char("Out-Flag")
    otHours = fields.float(string = "Out-Time")
     
    
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
