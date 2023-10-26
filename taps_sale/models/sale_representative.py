import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError




class TeamTeam(models.Model):
    _name = 'sale.team'
    _rec_name= 'team_name'
    _description = 'Sale Team'

    team_name= fields.Char(string='Team')
    # team_region = fields.Many2one('team.region',string='Team Region')
    # team_leader = fields.Many2one('sale.representative',string='Team Leader')


class TeamRegion(models.Model):
    _name = 'team.region'
    _rec_name= 'team_region'
    _description = 'Region'

    team_region = fields.Char(string='Team Region')

class TeamTransfer(models.Model):
    _name = 'team.transfer'
    _rec_name= 'name'
    _description = 'Team Transfer'

    name = fields.Char()
    sales_rep = fields.Many2one('sale.representative', string="Sale Representative")
    new_team =  fields.Many2one('sale.team', string="New Team")
    activation_date = fields.Date(string="Active From")
    state = fields.Selection([
        ('draft', 'DRAFT'),
        ('submit', 'SUBMIT'),
        ('confirm', 'DONE'),
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft', help="Status of the Team Transfer.")


    def button_confirm(self):
        raise UserError(self)
        # self.write({'state': 'confirm'})
        docs = self.env['sale.representative'].search([('id', '=', self.sales_rep.id), ('active', '=', True)])
        return self._create_and_deactive(docs)
        
    def button_submit(self):
        self.write({'state': 'submit'})
        return {}
        

    def _create_and_deactive(self,docs):

        for rec in docs:
            a=rec.create({'name':rec.name,'active':True,'team_activation_date': rec.activation_date})
            rec.update({'active':False, 'team_deact_date': rec.activation_date})
        return a


class SalesRepresentative(models.Model):
    _name = 'sale.representative'
    _rec_name= 'name'
    _description = 'Sales Person List'
    
    name = fields.Char(string='Sales Representative')
    leader = fields.Many2one('sale.representative', string="Team Leader")
    team = fields.Many2one('sale.team', string="Team")
    region = fields.Many2one('team.region', string="Region")
    # leader = fields.Many2one('team.team_leader', string="Team Leader")
    # region = fields.Many2one('team.region', string="Region")
    email = fields.Char(string='Email', help='Email address')
    related_employee = fields.Many2one('hr.employee', string="Related Employee")
    active = fields.Boolean(string="Active", default=True)
    team_activation_date = fields.Date(string="Team member since")
    team_deact_date = fields.Date(string="Deactivate Date")
    
    
    
    

