import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class SalesRepresentative(models.Model):
    _name = 'sale.representative'
    _rec_name= 'name'
    _description = 'SalesPerson List'
    
    name = fields.Char(string='Sales Representative')