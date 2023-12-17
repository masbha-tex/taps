# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError

class OrderModificationConfirmation(models.TransientModel):
    _name = 'oa.modification.confirmation'
    _description = 'Confirmation for Order Modification'

    order_id = fields.Many2one('sale.order', string='OA', readonly=True)

    @api.model
    def default_get(self, fields):
        # raise UserError(('fefef'))
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        order = self.env["sale.order"].browse(active_id)
        res["order_id"] = active_id
        return res

    # def _check_less_quantities_than_expected(self, pickings):
    #     for pick_id in pickings:
    #         moves_to_log = {}
    #         for move in pick_id.move_lines:
    #             if float_compare(move.product_uom_qty,
    #                              move.quantity_done,
    #                              precision_rounding=move.product_uom.rounding) > 0:
    #                 moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
    #         if moves_to_log:
    #             pick_id._log_less_quantities_than_expected(moves_to_log)

    def process(self):
        return self.order_id.cancel_confirm(True)

    def process_cancel(self):
        return self.order_id.cancel_confirm(False)

    def cancel(self):
        return False

