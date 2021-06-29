from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")

    def _compute_landed_cost_and_unit_value(self):
        for product in self:
            related_quant = self.env['stock.quant'].search([('product_id', '=', product.id), ('location_id.usage', '=', 'internal'),
                ('create_date', '<=', self.env.context.get('to_date')), ('lot_id', '!=', False)])
            if related_quant:
                product.landed_cost = sum(related_quant.mapped('landed_cost'))
                product.total_unit_value = sum(related_quant.mapped('total_unit_value'))
                product.unit_value = sum(related_quant.mapped('unit_value'))
            else:
                product.landed_cost = 0
                product.total_unit_value = 0
                product.unit_value = 0
