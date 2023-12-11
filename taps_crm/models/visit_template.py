
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, api


class VisitPurpose(models.Model):
    _name = 'crm.visit.purpose'
    _description = 'Visit Purposes'

    name = fields.Char(string="Purpose/Objective")
    
class CustomerVisit(models.Model):

    _name = 'crm.visit'
    _description = 'Customer Visit Template'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']


    name = fields.Char(string="Name")
    partner_id = fields.Many2one('res.partner', string='Customer')
    buyer = fields.Many2one('res.partner', string='Buyer')
    concern = fields.Char(string="Concern")
    designation = fields.Char(string="Designation")
    mobile = fields.Char(string="Mobile")
    product = fields.Char(string="Product")
    visit_purpose = fields.Many2one('crm.visit.purpose',string="Visit Purpose")
    visit_outcome = fields.Char(string="Visit Outcome")
    action = fields.Char(string="Action")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True, default=lambda self: self.env.user)
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', index=True, tracking=True,
        compute='_compute_team_id', readonly=False, store=True)
    stages = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),], 
        string='Status', copy=False, index=True, tracking=2, default='draft')





    @api.depends('user_id')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
                continue
            # team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=None)
            lead.team_id = team.id