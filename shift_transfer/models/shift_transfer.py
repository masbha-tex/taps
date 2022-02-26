# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
#from odoo.addons.hr.models.hr_employee import hr_employee

class ShiftTransfer(models.Model):
    _name = 'shift.transfer'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']    
    _description = 'Shift Transfer'
    
    #@api.onchange('empid')
    #def onchange_empid(self):
        #for rec in self:
            #return {'domain':{'name':[('emp_id','like', rec.empid)]}}

    code = fields.Char(string='Code', store=True, readonly=True)
    name = fields.Many2one('hr.employee', string='Employees')
    #empid = fields.Char(string='Employee ID', store=True, readonly=False)
    activationDate = fields.Date(string='Activation Date')
    transferGroup = fields.Many2one('shift.setup', string='Shift Transfer Group')
    inTime = fields.Float(related= 'transferGroup.inTime', related_sudo=False, string='In-Time')
    outTime = fields.Float(related= 'transferGroup.outTime', related_sudo=False, string='Out-Time')
    graceinTime = fields.Float(related= 'transferGroup.graceinTime', related_sudo=False, string="Grace In-Time")
        