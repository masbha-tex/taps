from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    itemtype = fields.Selection([
        ('raw', 'Raw Materials'),
        ('spares', 'Spares'),
        ('machinery', 'Capex (Machinery)'),
        ('consumable', 'Consumable'),
        ('capexit', 'Capex (IT Item)'),
        ('capexothers', 'Capex (Others)'),
        ('stationaryadmin', 'Stationary (Admin)'),
        ('stationaryothers', 'Stationary (Others)'),
        ('othersitem', 'Others Item'),
        ('civil', 'Project (Civil)'),
        ('chemicaltest', 'Chemical Test')
    ], string='Item Type', index=True, tracking=True, store=True, copy=True)
