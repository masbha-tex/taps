from odoo import models, fields, api


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
#     _description = 'hr_attendance_new_columns.hr_attendance_new_columns'

    attDate = fields.Date(string = "Date")
    inTime = fields.Float(string = "In-Time")
    inFlag = fields.Char("In-Flag")
    outTime = fields.Float(string = "Out-Time")
    outFlag = fields.Char("Out-Flag")
    otHours = fields.Float(string = "OT Hours")    
    
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
