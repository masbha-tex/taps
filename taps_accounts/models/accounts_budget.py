# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    itemtype = fields.Selection([
        ('raw', 'Raw Materials'),
        ('spares', 'Spares')
    ], string='Item Type', index=True, store=True, copy=True)
    product_id = fields.Many2one('product.product', string="Product_id")

    
    def duplicate_line(self):
        for line in self:
            new_line = line.copy()
            # Modify any fields on the copied line if needed
        return True


        
