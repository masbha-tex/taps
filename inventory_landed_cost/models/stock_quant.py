from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = "stock.quant"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_value", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total Unit Value", compute="_compute_value", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit Value", compute="_compute_value", groups="stock.group_stock_manager")
    product_category = fields.Many2one("product.category", related="product_id.categ_id", store=True)

    def _compute_value(self):
        # overriden from stock.quant._compute_value
        super()._compute_value()
        for quant in self:
            company_id = quant.company_id
            quant.landed_cost = 0
            if quant.lot_id:
                qty_sum = sum(self.env['stock.quant'].search([('lot_id', '=', quant.lot_id.id), ('location_id.usage', '=', 'internal')]).mapped('quantity'))
                quant.landed_cost = (quant.quantity / qty_sum) * quant.lot_id.landed_cost_total if qty_sum != 0 else 0

            quant.unit_value = (quant.value - quant.landed_cost) / quant.quantity
            quant.total_unit_value = quant.value / quant.quantity
