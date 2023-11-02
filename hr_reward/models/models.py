# -*- coding: utf-8 -*-

# from odoo import models, fields, api
# from odoo.exceptions import ValidationError, UserError


# class HrReward(models.Model):
#     _name = 'hr.reward'
#     _description = 'Employee Reward & Recognition'

    # name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    # employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)
    # company_id = fields.Many2one(related='employee_id.company_id', store=True)
    # department_id = fields.Many2one(related='employee_id.department_id', store=True)
    # submit_by = fields.Many2one('hr.employee',"Recommended By", required=True, default=lambda self: self.env.user.employee_id, tracking=True)
    # issue_date = fields.Date('Issue date', required=True, default=fields.Date.today())
    # details = fields.Html('Reward For', tracking=True, default="""
    #                 <div style="margin:0px;padding: 0px;">
    #                 <br>
    #                 <br>
    #                 <br>                    
    #                 </div>
    #                     """)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', _('New')) == _('New'):
    #         issue_date = vals.get('issue_date')
    #         vals['name'] = self.env['ir.sequence'].next_by_code('hr.reward', sequence_date=issue_date)
    #     return super(HrReward, self).create(vals)

#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
