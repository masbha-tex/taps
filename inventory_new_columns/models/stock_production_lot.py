from odoo import models, fields, api, _


class StockProductionlot(models.Model):
    _inherit = 'stock.production.lot'

    landed_cost_total = fields.Float(string="Total Landed Cost", compute="_compute_landed_cost_total")

    @api.depends('product_id.stock_valuation_layer_ids')
    def _compute_landed_cost_total(self):
        company_id = self.env.company.id
        domain = [
            ('product_id', '=', self.product_id.id),
            ('company_id', '=', company_id),
            ('stock_landed_cost_id', '!=', False)
        ]
        products = self.browse()
        groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum'], ['product_id', 'stock_move_id'], lazy=False)  # valuations with landed cost
        self.landed_cost_total = 0
        for group in groups:
            landed_cost = group['value']
            move = self.env['stock.move'].browse(group['stock_move_id'][0])
            if not move.lot_ids:
                continue  # skip if move not involving lots
            domain_2 = [('move_id', '=', move.id)]
            move_lines = move.move_line_ids.read_group(domain_2, ['qty_done:sum'], groupby=['lot_id'])
            for line in move_lines:
                ld_cost_split = (line['qty_done'] / move.quantity_done) * landed_cost  # ratio of qty done for each line to the LC distribution
                # self.env['stock.production.lot'].browse(line['lot_id'][0]).landed_cost_total = ld_cost_split  # give the landed cost total
                lot = self.env['stock.production.lot'].browse(line['lot_id'][0])
                lot.landed_cost_total = ld_cost_split
