# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ShiftSetup(models.Model):
    _name = 'shift.setup'
    _description = 'Shift Setup'

    code = fields.Char('Code')
    name = fields.Char(string="Shift Name")
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)
    inTime = fields.Float(string="In-Time")
    outTime = fields.Float(string="Out-Time")
    graceinTime = fields.Float(string="Grace In-Time")
    lunchinTime = fields.Float(string="Lunch In-Time")
    lunchoutTime = fields.Float(string="Lunch Out-Time")
    generalOT = fields.Float(string="General OT End Time")
    excessOT = fields.Float(string="Excess OT End Time")
    
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
