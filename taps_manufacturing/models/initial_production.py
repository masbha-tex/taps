import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from werkzeug.urls import url_encode
from datetime import datetime

class InitialProduction(models.Model):
    _name = "initial.production"
    _description = "Initial Production"
    _check_company_auto = True
    
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    product_tmpl_id = fields.Many2one('product.template', 'Template Id', store=True)
    product_name = fields.Char(related='product_tmpl_id.name', string='Product', store=True)
    fg_categ_type = fields.Char(string='Item', store=True)#related='product_tmpl_id.fg_categ_type', 
    production_date = fields.Datetime(string='Production Date')
    production_till_date = fields.Float(string='Comul. Production')
    invoice_till_date = fields.Float(string='Comul. Invoiced')
    released_till_date = fields.Float(string='Comul. Released')

