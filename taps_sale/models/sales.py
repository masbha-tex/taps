# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re


from werkzeug.urls import url_encode

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    topbottom = fields.Text(string='Top/Bottom', compute='_compute_topbottom', store=True, readonly=True)
    slidercode = fields.Text(string='Slider Code', compute='_compute_slidercode', store=True, readonly=True)
    finish = fields.Text(string='Finish', compute='_compute_finish', store=True, readonly=True)
    shade = fields.Text(string='Shade', compute='_compute_shade', store=True, readonly=True)
    sizein = fields.Text(string='Size (Inch)', compute='_compute_sizein', store=True, readonly=True)
    sizecm = fields.Text(string='Size (CM)', compute='_compute_sizecm', store=True, readonly=True)
    sizemm = fields.Text(string='Size (MM)', compute='_compute_sizemm', store=True, readonly=True)
    logoref = fields.Text(string='Logo & Ref', compute='_compute_logoref', store=True, readonly=True)
    shapefin = fields.Text(string='Shape Finish', compute='_compute_shapefin', store=True, readonly=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', compute='_compute_bcdpart', store=True, readonly=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', compute='_compute_nailmat', store=True, readonly=True)
    nailcap = fields.Text(string='Nail Cap Logo', compute='_compute_nailcap', store=True, readonly=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', compute='_compute_fnamebcd', store=True, readonly=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', compute='_compute_nu1washer', store=True, readonly=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', compute='_compute_nu2washer', store=True, readonly=True)    
    
    
    @api.depends('name')
    def _compute_topbottom(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Top / Bottom':
                        line.topbottom = kv
                        
                #raise UserError((h)) product_attribute_value attribute_id Size (Inch/cm)
    @api.depends('name')
    def _compute_slidercode(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Slider Code':
                        line.slidercode = kv
                        
    @api.depends('name')
    def _compute_finish(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Finish':
                        line.finish = kv
                        
    
    @api.depends('name')
    def _compute_shade(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Shade':
                        line.shade = kv
                        
                        
    @api.depends('name')
    def _compute_sizein(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Size (Inch)':
                        line.sizein = kv
    
    @api.depends('name')
    def _compute_sizecm(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Size (CM)':
                        line.sizecm = kv
    
    @api.depends('name')
    def _compute_sizemm(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Size (MM)':
                        line.sizemm = kv

    @api.depends('name')
    def _compute_logoref(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Logo & Ref':
                        line.logoref = kv
    
    @api.depends('name')
    def _compute_shapefin(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Shape Finish':
                        line.shapefin = kv
    
    @api.depends('name')
    def _compute_bcdpart(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'BCD Part Material Type / Size':
                        line.bcdpart = kv
    
    @api.depends('name')
    def _compute_nailmat(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Nail Material / Type / Shape / Size':
                        line.nailmat = kv
    
    @api.depends('name')
    def _compute_nailcap(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Nail Cap Logo':
                        line.nailcap = kv

    @api.depends('name')
    def _compute_fnamebcd(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == 'Finish Name ( BCD/NAIL/ NAIL CAP)':
                        line.fnamebcd = kv
    
    @api.depends('name')
    def _compute_nu1washer(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == '1 NO. Washer Material & Size':
                        line.nu1washer = kv
    
    @api.depends('name')
    def _compute_nu2washer(self):
        for line in self:
            if line.name and line.name.find("(")>0:
                b = line.name
                c = len(b)
                d = b.index("(")
                e = b.index(")")
                f = c-d-1
                g = c-e
                h = b[-f:-g]
                #line.topbottom = h
                for kv in h.split(","):
                    atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
                    satv = atv.sorted(key = 'attribute_id')[:1]
                    at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
                    if at.name == '2 NO. Washer Material & Size':
                        line.nu2washer = kv

    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        return product.get_product_multiline_description_sale()# + self._get_sale_order_line_multiline_description_variants()