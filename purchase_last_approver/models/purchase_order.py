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
        groups = self.env['studio.approval.entry'].read_group(domain, ['user_id:array_agg'], ['res_id'], orderby="create_date")
        purchase_last_approver = {i['res_id']: i['user_id'][-1] for i in groups}
        User = self.env['res.users']
        for rec in self:
            rec.last_approver = User.browse(purchase_last_approver[rec.id]) if rec.id in purchase_last_approver else False
