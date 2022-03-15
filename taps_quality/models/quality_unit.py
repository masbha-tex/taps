import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR





class QualityUnit(models.Model):
    _name = "quality.unit"
    _description = "Quality Unit"
    _rec_name = "unit_name"
    
    
    unit_name = fields.Char(string="Unit Name")