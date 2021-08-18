from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    last_approver = fields.Many2one(
        string="Last Approver",
        comodel_name="res.users",
        compute="_compute_last_approver",
    )

    def _compute_last_approver(self):
        domain = ['&', '&', ('model', '=', 'purchase.order'), ('res_id', 'in', self.ids), ('approved', '=', 'True')]

        # NOTE: previously use approach with using user_id. However due to different version of PostgreSQL lead to different order of ids retrieved using read_group()

        # dictionary of document (purchase.order) -> latest approved entry
        Entry = self.env['studio.approval.entry'].sudo()
        groups = Entry.read_group(domain, ['max_id:max(id)'], ['res_id'])
        purchase_last_approver = {i['res_id']: i['max_id'] for i in groups}
        for rec in self:
            rec.last_approver = Entry.browse(purchase_last_approver.get(rec.id, 0)).user_id
