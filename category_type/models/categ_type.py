# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError

class TypeofCategory(models.Model):
    _name = 'category.type'
    _description = 'Type of Categories'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char('Type of Categories', required=True, index=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        store=True)
    parent_id = fields.Many2one('category.type', 'Parent Type', index=True, ondelete='cascade')
    parent_path = fields.Char(index=True)
    child_id = fields.One2many('category.type', 'parent_id', 'Child Type')    
    company_id = fields.Many2one(
        'res.company', 'Company', required=True,
        default=lambda s: s.env.company.id, index=True)
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name