# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare

class OaUpdateConfirmation(models.TransientModel):
    _name = 'oa.update.confirmation'
    _description = 'OA Update Confirmation'

    oa_id = fields.Many2one('sale.order')

    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        order = self.env[""+active_model+""].browse(active_id)
        res["oa_id"] = order.id
        return res

    

    def confirm_oa(self):
        mo_ids = self.env.context.get("active_id")
        production = self.env["operation.details"].browse(mo_ids)
        production.set_group_output(mo_ids,self.qty)
        return True

    def process_cancel_backorder(self):
        return True

