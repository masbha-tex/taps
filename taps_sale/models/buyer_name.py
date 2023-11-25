import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class BuyerName(models.Model):
    _name = 'sale.buyer'
    _rec_name= 'name'
    _description = 'Buyer List'
    
    name = fields.Char(string='Buyer Name')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_buyer = fields.Boolean(string='Is Buyer')