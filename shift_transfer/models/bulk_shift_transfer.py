# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
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
        
#     @api.model
#     def create(self, vals):
#         raise UserError((self.activationDate))
#         for st in self.emp_ids:
# #             raise UserError((st))
#             self.env['shift.transfer'].create({
#                             'name': st.id,
#                             'empid': st.pin,
#                             'activationDate': self.activationDate,
#                             'transferGroup': self.transferGroup,
#                             'inTime': self.inTime,
#                             'outTime': self.outTime,
#                             'graceinTime': self.graceinTime,
#                         })
#         return super().create(vals)
    
    
    def bulk_to_shingle_transfer(self,emp_ids,activationDate,transferGroup,inTime,outTime,graceinTime):
        ii=0
        for st in emp_ids:
            self.env['shift.transfer'].create({
                            'name': st.id,
                            'empid': st.pin,
                            'activationDate': activationDate,
                            'transferGroup': transferGroup.id,
                            'inTime': inTime,
                            'outTime': outTime,
                            'graceinTime': graceinTime,
                        })