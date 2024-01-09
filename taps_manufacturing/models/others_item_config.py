import json
import datetime
import math
import operator as py_operator
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import format_date


class OthersItemConfig(models.Model):
    _name = "others.item.config"
    _description = "Others Item Configuration"
    _check_company_auto = True
    
    others_item = fields.Char(string='Others Item', store=True)
    product_tmpl_id = fields.Many2one('product.template', 'Template Id', store=True)
    product_name = fields.Char(related='product_tmpl_id.name', string='Product')
    unit = fields.Char(string='Unit')
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    # fg_categ_type = fields.Char(string='product_tmpl_id', store=True)

