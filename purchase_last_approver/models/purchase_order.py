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
        # create dictionary of purchase.order res_id: last approver user_id
        groups = self.env['studio.approval.entry'].sudo().read_group(domain, ['ids:array_agg(id)'], ['res_id'])
        purchase_last_approver = {i['res_id']: max(i['ids']) for i in groups}
        # User = self.env['res.users']
        Entry = self.env['studio.approval.entry']
        for rec in self:
            # rec.last_approver = User.browse(purchase_last_approver[rec.id]) if rec.id in purchase_last_approver else False
            rec.last_approver = Entry.browse(purchase_last_approver[rec.id]).user_id if rec.id in purchase_last_approver else False
