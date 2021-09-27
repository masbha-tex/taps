# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ShiftTransfer(models.Model):
    _name = 'shift.transfer'
    _description = 'Shift Transfer'

    code = fields.Char(string='Code', readonly=True)
    name = fields.Many2one('hr.employee', string='Employee')
    activationDate = fields.Date(string='Activation Date')
    transferGroup = fields.Many2one('shift.setup', string='Shift Transfer Group')

