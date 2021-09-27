# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ShiftTransfer(models.Model):
    _name = 'shift.transfer'
    _description = 'Shift Transfer'

    code = fields.Char(string='Code', readonly=True)
    name = fields.Many2one('hr.employee', string='Employee')
    #empID = fields.Many2one(related= 'name.x_studio_employee_id', related_sudo=False, string='Employee ID')
    activationDate = fields.Date(string='Activation Date')
    transferGroup = fields.Many2one('shift.setup', string='Shift Transfer Group')
    inTime = fields.Char(related= 'transferGroup.inTime', string='In-Time')
    outTime = fields.Char(related= 'transferGroup.outTime', string='Out-Time')
