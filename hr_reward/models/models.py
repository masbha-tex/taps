# -*- coding: utf-8 -*-

# from odoo import models, fields, api
# from odoo.exceptions import ValidationError, UserError


# class hr_reward(models.Model):
#     _name = 'hr.reward'
#     _description = 'Employee Reward & Recognition'

    # name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    # employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)
    # company_id = fields.Many2one(related='employee_id.company_id', store=True)
    # department_id = fields.Many2one(related='employee_id.department_id', store=True)

#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
