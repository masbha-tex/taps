import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR





class Parameter(models.Model):
    _name = "quality.parameter"
    _description = "Quality Parameter"
    _rec_name = "parameter_name"
            
           
    parameter_name = fields.Char(string="Parameter Name")
    initial_value = fields.Float(string='Lower Value')
    last_value = fields.Float(string='Higher Value')
    
    quality_category = fields.Many2one('product.category')
    quality_unit = fields.Many2one('quality.unit')
    unit_name = fields.Char(related='quality_unit.unit_name')
    t_level = fields.Char(compute='_compute_level', store="False")
    note = fields.Char(string='Note')
    
    @api.depends('initial_value', 'last_value','unit_name','note')
    def _compute_level(self):    
        for record in self:
            s1=str(record.initial_value)
            s2=str(record.last_value)
            s3=str(record.unit_name)
            s4=record.note
            if(record.initial_value == 0 and record.last_value != 0):
                record.t_level = "≤"+s2+" "+s3
            if(record.initial_value != 0 and record.last_value == 1000):
                record.t_level = "≥"+ s1+" "+s3
            if(record.initial_value !=0 and record.last_value!=1000):
                record.t_level = "["+s1+" to "+s2+"] "+s3
            if(record.initial_value == 0 and record.last_value == 0):
                record.t_level = s4
    
    
    

    
