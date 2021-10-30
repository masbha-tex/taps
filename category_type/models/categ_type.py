# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError

class TypeofCategory(models.Model):
    _name = 'category.type'
    _description = 'Type of Categories'

    name = fields.Char('Type of Categories', required=True, translate=True)
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.company.id, index=True)