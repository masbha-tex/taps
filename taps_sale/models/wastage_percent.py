import ast
import json
from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR



class WastagePercent(models.Model):
    _name = 'wastage.percent'
    _description = 'Production Wastage Percent for BOM Computation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    
    product_type = fields.Text(string='Type', required=True)
    material = fields.Text(string='Material', required=True)
    wastage = fields.Float('Wastage Percent', required=True, default=0)