# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    itemtype = fields.Selection([
        ('raw', 'Raw Materials'),
        ('spares', 'Spares')
    ], string='Item Type', index=True, tracking=True, store=True, copy=True)
