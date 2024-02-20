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

class FgPackaging(models.Model):
    _name = "fg.packaging"
    _description = "FG Packaging"
    _check_company_auto = True

   
    name = fields.Char(string='Carton')
    internal_ref = fields.Char(string='Carton No', store=True)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    packaging_line = fields.One2many('fg.packaging.line', 'packaging_id', string='Line',copy=True, auto_join=True)
    total_weight = fields.Char(string='Approximate Total Weight')
    total_qty = fields.Integer(string='Total Qty', store=True)
    total_pack = fields.Integer(string='Total Pack', store=True)
    customer_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    # customer_id = fields.Char(string='Customer')
    
    # @api.model
    def name_get(self):
        result = []
        for packaging in self:
            name = packaging.internal_ref
            if not name:
                name = packaging.name
            result.append((packaging.id, name))
        return result
        
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        seq_date = None
        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.now()))
        if 'name' in vals:
            if vals.get('name'):
                vals['internal_ref'] = vals.get('name')
                
        ref = self.env['ir.sequence'].next_by_code('fg.cartoon', sequence_date=seq_date)
        vals['name'] = ref
        result = super(FgPackaging, self).create(vals)
        return result        

    
class FgPackagingLine(models.Model):
    _name = "fg.packaging.line"
    _description = "Packaging Line"
    _check_company_auto = True
    
    l_code = fields.Many2one('operation.details', string='L Code', store=True)
    oa_id = fields.Char(string='OA',store=True)
    packaging_id = fields.Many2one('fg.packaging', string='Carton No', ondelete='cascade')    
    product_id = fields.Char(string='product_id',store=True)
    product_template_id = fields.Char(string='product_template_id',store=True)
    action_date = fields.Datetime(string='action_date',store=True)
    shade = fields.Char(string='shade',store=True)
    shade_ref = fields.Char(string='shade_ref',store=True)
    finish = fields.Char(string='finish',store=True)
    slidercodesfg = fields.Char(string='slidercodesfg',store=True)
    top = fields.Char(string='top',store=True)
    bottom = fields.Char(string='bottom',store=True)
    pinbox = fields.Char(string='pinbox',store=True)
    sizcommon = fields.Char(string='sizcommon',store=True)
    qty = fields.Char(string='qty',store=True)


    # @api.onchange('l_code')
    # def onchange_l_code(self):
    #     if self.l_code:
    #         operation_details = self.l_code
    #         self.oa_id = operation_details.oa_id.name
    #         # self.fg_carton = operation_details.fg_carton
    #         self.product_id = operation_details.product_id
    #         self.product_template_id = operation_details.product_template_id
    #         self.action_date = operation_details.action_date
    #         self.shade = operation_details.shade
    #         self.shade_ref = operation_details.shade_ref
    #         self.finish = operation_details.finish
    #         self.slidercodesfg = operation_details.slidercodesfg
    #         self.top = operation_details.top
    #         self.bottom = operation_details.bottom
    #         self.pinbox = operation_details.pinbox
    #         self.sizcommon = operation_details.sizcommon
    #         self.qty = operation_details.done_qty