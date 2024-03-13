# -*- coding: utf-8 -*-

# from odoo import models, fields, api, _ 
# from odoo.exceptions import ValidationError, UserError

# class HrAuditCertification(models.Model):
#     _name = 'hr.audit.certification'
#     _description = 'Audit Certification'
      # _inherit = ['mail.thread', 'mail.activity.mixin']  

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
