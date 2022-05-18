# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
#from odoo.addons.hr.models.hr_employee import hr_employee

class ShiftTransfer(models.Model):
    _name = 'shift.transfer.bulk'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']    
    _description = 'Bulk Shift Transfer'
    
    #@api.onchange('empid')
    #def onchange_empid(self):
        #for rec in self:
            #return {'domain':{'name':[('emp_id','like', rec.empid)]}}

    code = fields.Char(string='Code', store=True, readonly=True)
    
    emp_ids = fields.Many2many('hr.employee', string='Employees',copy=False)    
#     name = fields.Many2one('hr.employee', string='Employees')
#     empid = fields.Char(related= 'name.pin', related_sudo=False, string='Employee ID')
    activationDate = fields.Date(string='Activation Date')
    transferGroup = fields.Many2one('shift.setup', string='Shift Transfer Group')
    inTime = fields.Float(related= 'transferGroup.inTime', related_sudo=False, string='In-Time')
    outTime = fields.Float(related= 'transferGroup.outTime', related_sudo=False, string='Out-Time')
    graceinTime = fields.Float(related= 'transferGroup.graceinTime', related_sudo=False, string="Grace In-Time")
        
    @api.model
    def create(self, vals):
        for st in vals.emp_ids:
            self.env['shift.transfer'].create({
                            'name': st.id,
                            'empid': st.pin,
                            'activationDate': vals.activationDate,
                            'transferGroup': vals.transferGroup,
                            'inTime': vals.inTime,
                            'outTime': vals.outTime,
                            'graceinTime': vals.graceinTime,
                        })
        return super().create(vals)