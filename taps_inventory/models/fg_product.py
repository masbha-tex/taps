import ast
import json
from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR



class ProductBomFormula(models.Model):
    _name = 'fg.product.formula'
    _description = 'It is a formula table for bom computation'
    
    #id, product_id, name, unit
    product_id = fields.Integer(string='Product Id')
    product_name = fields.Char(string='Name')
    product_type = fields.Char(required=True)
    unit_type = fields.Char(required=True)
    amount_python_compute = fields.Text(string='Python Code')