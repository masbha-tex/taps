from odoo import models, fields, api, _


class ProductProduct(models.Model):
    _inherit = "product.product"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost_rev", groups="stock.group_stock_manager")

    @api.depends('stock_valuation_layer_ids')
    def _compute_landed_cost(self):
        company_id = self.env.company.id
        domain = [
            ('product_id', 'in', self.ids),
            ('company_id', '=', company_id),
            ('stock_landed_cost_id', '!=', False)
        ]
        products = self.browse()
        # import pudb;pudb.set_trace()
        groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum'], ['product_id'])
        for group in groups:
            product = self.browse(group['product_id'][0])
            company_currency = self.env.company.currency_id.round(group['value'])
            if product.quantity_svl:
                product.landed_cost = company_currency / product.quantity_svl
            else:
                product.landed_cost = company_currency

            products |= product

        remaining = (self-products)
        remaining.landed_cost = 0


    @api.depends('stock_valuation_layer_ids')
    def _compute_landed_cost_rev(self):
        # import pudb;pudb.set_trace()
        company_id = self.env.company.id
        domain = [
            ('product_id', 'in', self.ids),
            ('company_id', '=', company_id),
            ('stock_landed_cost_id', '!=', False)
        ]
        products = self.browse()
        groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum'], ['product_id', 'stock_move_id'], lazy=False)  # valuations with landed cost

        for group in groups:
            landed_cost = group['sum']
            move = self.env['stock.move'].browse(group['stock_move_id'])
            if not move.lot_ids:
                continue  # skip if move not involving lots
            domain_2 = [('move_id', '=', move.id)]
            move_lines = move.move_line_ids.read_group(domain_2, ['qty_done:sum'], groupby=['lot_id'], lazy=False)
            for line in move_lines:
                ld_cost_split = (m.qty_done / move.quantity_done) * landed_cost  # ratio of qty done for each line to the LC distribution
                env['stock.production.lot'].browse(line['lot_id'][0]).landed_cost_total = ld_cost_split  # give the landed cost total
