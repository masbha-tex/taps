# -*- coding: utf-8 -*-
from odoo import models, fields, api
#from odoo.addons.hr.models.hr_employee import hr_employee

class ShiftTransfer(models.Model):
    _name = 'shift.transfer'
    _description = 'Shift Transfer'

    code = fields.Char(string='Code', store=True)#readonly=True,
    name = fields.Many2one('hr.employee', string='Employee')
    empid = fields.Char(related= 'name.pin', related_sudo=False, string='Employee ID')
    activationDate = fields.Date(string='Activation Date')
    transferGroup = fields.Many2one('shift.setup', string='Shift Transfer Group')
    inTime = fields.Float(related= 'transferGroup.inTime', related_sudo=False, string='In-Time')
    outTime = fields.Float(related= 'transferGroup.outTime', related_sudo=False, string='Out-Time')
    graceinTime = fields.Float(related= 'transferGroup.graceinTime', related_sudo=False, string="Grace In-Time")