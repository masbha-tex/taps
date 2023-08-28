import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class SalesRepresentative(models.Model):
    _name = 'sale.representative'
    _rec_name= 'name'
    _description = 'SalesPerson List'
    
    name = fields.Char(string='Sales Representative')
    sales_representative_team = fields.Selection([
            ('jamuna', 'JAMUNA'),
            ('padma', 'PADMA'),
            ('sangu', 'SANGU'),
            ('shitolokkha', 'SHITOLOKKHA'),
            ('meghna', 'MEGHNA'),
            ('karnaphuli', 'KARNAPHULI'),
            ('brahmaputra', 'BRAHMAPUTRA'),],
            string='Team')
    
    sales_representative_position = fields.Selection([
            ('leader', 'Team Leader'),
            ('member', 'Team Member'),],
            string='Position')
    sales_representative_region = fields.Selection([
            ('export', 'EXPORT'),
            ('dhaka', 'DHAKA'),
            ('chittagong', 'CHITTAGONG'),],
            string='Region')