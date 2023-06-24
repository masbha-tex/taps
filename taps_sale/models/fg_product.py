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
    tbwire_python_compute = fields.Text(string='Top & Botom')
    topbottom_type = fields.Text(string='Type')
    tape_price= fields.Float('Tape Price', required=True, digits='Unit Price', default=0.0)
    slider_price= fields.Float('Slider Price', required=True, digits='Unit Price', default=0.0)
    wire_price= fields.Float('Wire Price', required=True, digits='Unit Price', default=0.0)
    topwire_price= fields.Float('Top Price', required=True, digits='Unit Price', default=0.0)
    botomwire_price= fields.Float('Bottom Price', required=True, digits='Unit Price', default=0.0)
    tbwire_price= fields.Float('Topbotom Price', required=True, digits='Unit Price', default=0.0)
    pinbox_price= fields.Float('Pinbox Price', required=True, digits='Unit Price', default=0.0)
    dyeing_charge= fields.Float('Dyeing Charge', required=True, digits='Unit Price', default=0.0)
    depping_charge= fields.Float('Depping Charge', required=True, digits='Unit Price', default=0.0)
    plating_charge= fields.Float('Plating Charge', required=True, digits='Unit Price', default=0.0)
    painting_charge= fields.Float('Painting Charge', required=True, digits='Unit Price', default=0.0)