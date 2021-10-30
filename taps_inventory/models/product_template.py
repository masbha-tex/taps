# -*- coding: utf-8 -*-
from odoo import models, fields, api

class IncludeCateTypeInPT(models.Model):
    _inherit = 'product.template'
    categ_type = fields.Many2one('category.type', 'Category Type', check_company=True)