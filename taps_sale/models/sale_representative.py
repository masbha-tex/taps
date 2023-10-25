import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError




class TeamTeam(models.Model):
    _name = 'sale.team'
    _rec_name= 'team_name'
    _description = 'Sale Team'

    team_name= fields.Char(string='Team')


class TeamRegion(models.Model):
    _name = 'team.region'
    _rec_name= 'team_region'
    _description = 'Region'

    team_region = fields.Char(string='Team Region')




class SalesRepresentative(models.Model):
    _name = 'sale.representative'
    _rec_name= 'name'
    _description = 'SalesPerson List'
    
    name = fields.Char(string='Sales Representative')
    leader = fields.Many2one('sale.representative', string="Team Leader")
    team = fields.Many2one('sale.team', string="Team")
    region = fields.Many2one('team.region', string="Region")
    email = fields.Char(string='Email', help='Email address')
    related_employee = fields.Many2one('hr.employee', string="Related Employee")
    active = fields.Boolean(string="Active", default=True)
    
    
    
    

