import ast
import json
from datetime import datetime

from odoo import api, fields, models, _, SUPERUSER_ID
from odoo.exceptions import UserError
from odoo.osv.expression import OR



class ProductBomFormula(models.Model):
    _name = 'fg.product.formula'
    _description = 'It is a formula table for bom computation'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    
    #id, product_id, name, unit
    product_tmpl_id = fields.Many2one('product.template', 'Product Id')
    product_name = fields.Char(related='product_tmpl_id.name', string='Name', store=True, readonly=True)
    product_type = fields.Text(string='Type', required=True)
    unit_type = fields.Text(string='Unit Type', required=True)
    tape_python_compute = fields.Text(string='Tap')
    wair_python_compute = fields.Text(string='Wire')
    slider_python_compute = fields.Text(string='Slider')
    twair_python_compute = fields.Text(string='Top Wire')
    bwire_python_compute = fields.Text(string='Botom Wire')
    pinbox_python_compute = fields.Text(string='Pin BOx')
    taffeta_python_compute = fields.Text(string='Taffeta')