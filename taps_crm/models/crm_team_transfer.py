import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class CrmTeamTransfer(models.Model):
    _name = "crm.team.transfer"
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Transfer To a new Sales Team"
    

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    date = fields.Date(string="Date", default=date.today())
    user_domain = fields.Char(compute="_compute_user",readonly=True, store=True)
    type = fields.Selection([
        ('add', 'ADD'),
        ('remove', 'Remove'),
        ('transfer', 'Transfer')
    ],string="Type", required=True)
    user_id = fields.Many2one('res.users', string="User")
    existing_team = fields.Many2one('crm.team', string="Existing Team", readonly=True)
    new_team = fields.Many2one('crm.team', string="New Team")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string="Status",  default='draft', tracking=True)
    explanation = fields.Text(string="Explanation", required=True)

    @api.onchange('user_id')
    def compute_team_id(self):
        
        team = self.env['crm.team'].search([('id', '=', self.user_id.sale_team_id.id)], limit=1)
        # raise UserError((team))
        self.existing_team= team.id

    @api.onchange('type')
    def _reset_all_attribute(self):
        for record in self:
            record.user_id = False
            record.existing_team = False
        
        

    @api.depends('user_id')
    def _compute_user(self):
        for record in self:
            if record.type == 'add':
                record.user_domain = json.dumps([('sale_team_id', '=', False)])
            elif record.type == 'remove':
                record.user_domain = json.dumps([('sale_team_id', '!=', False)])
            elif record.type == 'transfer':
                record.user_domain = json.dumps([('sale_team_id', '!=', False)])
        
    def action_submit_approval(self):
        self.write({'state':'submitted'})
        user = self.env['crm.approval.matrix'].search([('model_name', '=','crm.team.transfer')],limit=1)
        # raise UserError((user.first_approval.id))
        self.activity_schedule('taps_crm.mail_activity_team_transfer_first_approval', user_id=user.first_approval.id)
        

    def action_hod(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','crm.team.transfer')],limit=1)
        if user.first_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_team_transfer_first_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            self.write({'state':'to approve'})
            self.activity_schedule('taps_crm.mail_activity_team_transfer_final_approval', user_id=user.second_approval.id)
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))

    def action_approve(self):
        return {}

    def action_set_draft(self):
        return {}
    def action_cancel(self):
        return {}
    
    