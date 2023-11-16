# -*- coding: utf-8 -*-

# from odoo import models, fields, api


# class Document(models.Model):
    # _name = 'taps_documents.taps_documents'
    # _inherit = 'documents.document'
#     _description = 'Document'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100
