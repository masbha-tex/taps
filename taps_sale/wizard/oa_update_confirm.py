# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models
from odoo.tools.float_utils import float_compare
from odoo.exceptions import AccessError, UserError, ValidationError

class OaUpdateConfirmation(models.TransientModel):
    _name = 'oa.update.confirmation'
    _description = 'OA Update Confirmation'

    oa_id = fields.Many2one('sale.order', string='OA')

    @api.model
    def default_get(self, fields):
        # raise UserError(('rgwefwfe'))
        res = super().default_get(fields)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        order = self.env[""+active_model+""].browse(active_id)
        res["oa_id"] = order.id
        return res

    def confirm_oa(self):
        mo_ids = self.env.context.get("active_id")
        order = self.env["operation.details"].browse(mo_ids)
        order.set_update_confirm(mo_ids,self.qty)
        return True

    def process_cancel_backorder(self):
        return True

