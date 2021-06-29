from odoo import models, fields, api, _


class StockQuant(models.Model):
    _inherit = "stock.quant"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total Unit Value", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit Value", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    product_category = fields.Many2one("product.category", related="product_id.categ_id", store=True)

    def _compute_landed_cost(self):
        groups = self.read_group([('location_id.usage', '=', 'internal'), ('lot_id', 'in', self.lot_id.ids)], ['quantity:sum'], ['lot_id'])
        group_dict = {group['lot_id'][0]: group['quantity'] for group in groups}

        for quant in self:
            quantity = group_dict[quant.lot_id.id] if quant.lot_id else 0
            company_id = quant.company_id

            quant.landed_cost = (quant.quantity / quantity) * quant.lot_id.landed_cost_total if quantity != 0 else 0
            quant.unit_value = (quant.value - quant.landed_cost) / quant.quantity if quant.quantity != 0 else 0
            quant.total_unit_value = quant.value / quant.quantity if quant.quantity != 0 else 0
