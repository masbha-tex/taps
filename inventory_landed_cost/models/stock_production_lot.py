from odoo import models, fields, api, _


class StockProductionlot(models.Model):
    _inherit = 'stock.production.lot'

    landed_cost_total = fields.Float(string="Total Landed Cost", compute="_compute_landed_cost_total")

    @api.depends('product_id.stock_valuation_layer_ids')
    def _compute_landed_cost_total(self):
        company_id = self.env.company.id
        domain = [
            ('product_id', 'in', self.product_id.ids),
            ('company_id', '=', company_id),
            ('stock_landed_cost_id', '!=', False),
        ]
        # valuations with landed cost
        groups = self.env['stock.valuation.layer'].read_group(domain, ['value:sum'], ['product_id', 'stock_move_id'], lazy=False)
        Move = self.env['stock.move']
        MoveLine = self.env['stock.move.line']

        # store all moves that has lot_ids
        move_sum = {}
        for i in groups:
            move = Move.browse(i['stock_move_id'][0])
            if move.lot_ids:
                move_sum[move.id] = i['value'] / move.quantity_done
        move_ids = list(move_sum.keys())

        lot_group = MoveLine.read_group([('move_id', 'in', move_ids), ('lot_id', 'in', self.ids)], ['qty_done:sum'], ['lot_id', 'move_id'], lazy=False)
        lot_move_value = dict((i['lot_id'][0], (i['qty_done'], i['move_id'][0])) for i in lot_group)
        for rec in self:
            lot_done, lot_move_id = lot_move_value.get(rec.id, (0, 0))
            rec.landed_cost_total = lot_done * move_sum.get(lot_move_id, 0)
