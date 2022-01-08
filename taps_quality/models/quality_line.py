import ast

from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR

class QualityCheck(models.Model):
    _inherit = "quality.check"
    quality_check_line = fields.One2many('quality.check.line', 'check_id', string='Order Lines', copy=True)
    
    
    
    
class QualityCheckLine(models.Model):
    _name = 'quality.check.line'
    _description = 'Quality Check Details'

    name = fields.Char()
    check_id = fields.Many2one('quality.check', string='Check Reference', index=True, required=True, ondelete='cascade')
    parameter = fields.Text(string='Parameter')
    t_level = fields.Text(string='Tolarance')
    value1 = fields.Float(string='V1')
    value2 = fields.Float(string='V2')
    value3 = fields.Float(string='V3')
    value4 = fields.Float(string='V4')
    value5 = fields.Float(string='V5')
    value6 = fields.Float(string='V6')
    value7 = fields.Float(string='V7')
    value8 = fields.Float(string='V8')
    value9 = fields.Float(string='V9')
    value10 = fields.Float(string='V10')
    status = fields.Selection([
        ('ok', 'Ok'),
        ('notok', 'Not Ok'),
        ('nottested', 'Not Tested')], string='Status', tracking=True,
        default='nottested', copy=False)
    quality_category = fields.Selection([
        ('n3_long_chain', 'N#3 Long Chain'),
        ('n3_long_chain_grs', 'N#3 Long Chain Grs')], string='Quality Category', tracking=True,
        default='n3_long_chain', copy=False)
    
    

