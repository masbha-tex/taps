from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount
from datetime import date

class PurchaseReq(models.Model):
    _inherit = "approval.request"
    #_order = 'priority desc, id desc'
    
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)
    request_status = fields.Selection(selection_add=[('draft', 'Draft'),('new',)],default="new", compute="_compute_request_status")
    

    approver_ids = fields.One2many('approval.approver', 'request_id', string="Approvers", check_company=True)

    @api.depends('approver_ids.status')
    def _compute_request_status(self):
        for request in self:
            status_lst = request.mapped('approver_ids.status')
            minimal_approver = request.approval_minimum if len(status_lst) >= request.approval_minimum else len(status_lst)
            if status_lst:
                if status_lst.count('cancel'):
                    status = 'cancel'
                elif status_lst.count('refused'):
                    status = 'refused'
                elif status_lst.count('draft'):
                    status = 'draft'
                elif status_lst.count('approved') >= minimal_approver:
                    status = 'approved'
                elif status_lst.count('pending'):
                    status = 'pending'
                else:
                    status = 'draft'
            else:
                status = 'draft'
            # raise UserError((status))
            request.request_status = status

        self.filtered_domain([('request_status', 'in', ['approved', 'refused', 'cancel'])])._cancel_activities()

    def action_hop(self):
        self.write({'request_status': 'new'})
        return {}
        



    
class ApprovalCategory(models.Model):
    _inherit = 'approval.category'
    _description = 'Approval Category'
    _order = 'sequence'

    _check_company_auto = True


    def create_request(self):
        self.ensure_one()
        # If category uses sequence, set next sequence as name
        # (if not, set category name as default name).
        return {
            "type": "ir.actions.act_window",
            "res_model": "approval.request",
            "views": [[False, "form"]],
            "context": {
                'form_view_initial_mode': 'edit',
                'default_name': _('New') if self.automated_sequence else self.name,
                'default_category_id': self.id,
                'default_request_owner_id': self.env.user.id,
                'default_request_status': 'draft',
                'default_date' : date.today(),
            },
        }