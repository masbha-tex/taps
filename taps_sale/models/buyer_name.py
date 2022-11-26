import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR





class BuyerName(models.Model):
    _name = "sale.buyer"
    _description = "Buyer Name"
    
            
           
    buyer_name = fields.Char(string="Buyer Name")
    
    
    

    
