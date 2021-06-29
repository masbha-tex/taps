from odoo import fields, models


class Product(models.Model):
    _inherit = "product.product"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")

    def _compute_landed_cost_and_unit_value(self):
        domain = [
            ('location_id.usage', '=', 'internal'),
            ('create_date', '<=', self.env.context.get('to_date')),
            ('lot_id', '!=', False),
            ('product_id', 'in', self.ids),
        ]

        groups = self.env['stock.quant'].read_group(domain, ['ids:array_agg(id)'], ['product_id'])

        quant_ids = [g for group in groups for g in group['ids']]

        # map the landed_cost and cache it, so landed cost will not be computed everytime
        self.env['stock.quant'].browse(quant_ids).mapped('landed_cost')

        group_dict = {group['product_id'][0]: group['ids'] for group in groups}

        for product in self:
            quant = self.env['stock.quant']
            if group_dict.get(product.id):
                quant = quant.browse(group_dict[product.id])
            product.landed_cost = sum(quant.mapped('landed_cost'))
            product.total_unit_value = sum(quant.mapped('total_unit_value'))
            product.unit_value = sum(quant.mapped('unit_value'))
