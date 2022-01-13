import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR





class Parameter(models.Model):
    _name = "quality.parameter"
    _description = "Quality Parameter"
    _rec_name = "parameter_name"
    parameter_name = fields.Char(String="Parameter Name")
    quality_category_parameter = fields.Selection([
        ('n3_long_chain', 'N#3 Long Chain'),
        ('n3_long_chain_grs', 'N#3 Long Chain Grs')], string='Quality Category',
        default='n3_long_chain', copy=False)
    initial_value = fields.Float(string='Lower Value')
    
    last_value = fields.Float(string='Higher Value')
    
    t_level = fields.Text(compute='_compute_level', store="True")
    
    @api.depends('initial_value', 'last_value')
    def _compute_level(self):    
        for record in self:
            s1=str(record.initial_value)
            s2=str(record.last_value)
            record.t_level = s1+" to "+s2

    
    
    