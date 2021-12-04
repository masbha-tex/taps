# -*- coding: utf-8 -*-
from odoo import models, fields, api

class IncludeCateTypeInPT(models.Model):
    _inherit = 'product.template'
    categ_type = fields.Many2one('category.type', 'Category Type', check_company=True, change_default=True)
    
    pur_description = fields.Selection([
        ('spares', 'Spares'),
    ], string='PUR Description', store=False, readonly=False, copy=True)
    #description_purchase = fields.Text('Purchase Description', related='pur_description', translate=True)
    
    @api.onchange('pur_description')
    def onchange_pur_description(self):
        self.description_purchase = ''
        if self.pur_description !="":
            self.description_purchase = self.pur_description  