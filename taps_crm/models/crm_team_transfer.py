import json

from babel.dates import format_date
from datetime import date,datetime, timedelta
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class CrmTeamTransfer(models.Model):
    _name = "crm.team.transfer"
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Transfer To a new Sales Team"
    

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    eff_date = fields.Date(string="Effective Date", default=date.today())
    user_domain = fields.Char(compute="_compute_user",readonly=True, store=True)
    type = fields.Selection([
        ('add', 'ADD'),
        ('remove', 'Remove'),
        ('transfer', 'Transfer')
    ],string="Type", required=True, default='add')
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
    is_team_leader = fields.Boolean(string="Want To Make him Team Leader", default=False)

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
            record.is_team_leader = False
        
        

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
            raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))

    def action_approve(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','crm.team.transfer')],limit=1)
        if user.second_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_team_transfer_final_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            if self. type == "add":
                self._action_add()
                self._update_visit()
                self._update_sale_order()
            if self. type == "remove":
                self._action_remove()
                
            if self. type == "transfer":
                self.user_id.sale_team_id = self.new_team.id
            
            self.write({'state':'approved'})
        else:
            raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))

    def action_set_draft(self):
        self.write({'state':'draft'})
    def action_cancel(self):
        self.write({'state':'cancel'})

    def _action_add(self):
        if self.new_team.name == 'MARKETING':
            assign_user = self.env['buyer.allocated'].sudo().search([('id', '=', self.user_id.id)])
            if not assign_user:
                new_record = self.env['buyer.allocated'].sudo().create({'marketingperson' : self.user_id.id})
            else:
                raise UserError(("Already Exist in this Team"))
        else:
            assign_user = self.env['customer.allocated'].sudo().search([('id', '=', self.user_id.id)])
            if not assign_user:
                new_record = self.env['customer.allocated'].sudo().create({'salesperson' : self.user_id.id})
            else:
                raise UserError(("Already Exist in this Team"))
        self.user_id.sale_team_id = self.new_team.id
        if self.is_team_leader:
            self.new_team.user_id = self.user_id

    

    def _action_remove(self):
        if self.new_team.name == 'MARKETING':
            assign_user = self.env['buyer.allocated'].sudo().search([('id', '=', self.user_id.id)], limit=1)
            if assign_user:
                assign_user.active = False
        else:
            assign_user = self.env['customer.allocated'].sudo().search([('id', '=', self.user_id.id)], limit=1)
            if assign_user:
                assign_user.write({'active': True})
                
        self.user_id.sale_team_id = False
        if self.user_id.id == self.existing_team.user_id.id:
            # raise UserError((self.user_id,self.existing_team.user_id))
            self.existing_team.user_id = False
        

    def _update_visit(self):
        start_date = datetime.combine(self.eff_date, datetime.min.time())
        end_date = datetime.combine(self.eff_date, datetime.max.time())
        end_date += timedelta(days=1)
        visit = self.env['crm.visit'].sudo().search([('user_id', '=', self.user_id.id),('create_date', '>=',start_date),('create_date', '<', end_date)])
        for rec in visit:
            rec.write({'team_id': self.new_team.id})
            
    def _update_sale_order(self):
        start_date = datetime.combine(self.eff_date, datetime.min.time())
        end_date = datetime.combine(self.eff_date, datetime.max.time())
        end_date += timedelta(days=1)
        sale_order = self.env['sale.order'].sudo().search([('user_id', '=', self.user_id.id),('create_date', '>=',start_date),('create_date', '<', end_date)])
        for rec in sale_order:
            rec.write({'team_id': self.new_team.id, 'region_id': self.new_team.region_id.id})
        
            
                
        
    
    