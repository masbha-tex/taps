import base64

from odoo import api, models, fields, _
from odoo.exceptions import UserError
from odoo.tools.image import image_data_uri

import werkzeug
import werkzeug.exceptions




class Bank(models.Model):
    
    _inherit="res.bank"
    
    
    account_number = fields.Char(string='Account Number')
    routing_number = fields.Char(string='Routing Number')