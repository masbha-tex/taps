# -*- coding: utf-8 -*-
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


class CombineInvoice(models.Model):
    _name = "combine.invoice"
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Customer Invoice"
    _check_company_auto = False

    # ==== Business fields ====
    name = fields.Char(string='Number', copy=False, readonly=False, store=True, index=True, tracking=True)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, string='Currency')
    line_id = fields.One2many('combine.invoice.line', 'invoice_id', string='Customer Invoice Items', copy=True, readonly=True,)
    partner_id = fields.Many2one('res.partner', readonly=True ,string='Partner', states={'draft': [('readonly', False)]})
    # commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', store=True, readonly=True,
    #     compute='_compute_commercial_partner_id', ondelete='restrict')
    # country_code = fields.Char(related='company_id.country_id.code', readonly=True)
    # user_id = fields.Many2one(string='User', related='invoice_user_id',
    #     help='Technical field used to fit the generic behavior in mail templates.')
    
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank',store=True, readonly=False)
    payment_reference = fields.Char(string='Payment Reference', store=True, readonly=False)
    
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,)
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        readonly=True)
    # /!\ invoice_line_ids is just a subset of line_ids.
    # invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',
    #     copy=False, readonly=True,
    #     domain=[('exclude_from_invoice_tab', '=', False)],
    #     states={'draft': [('readonly', False)]})
    invoice_incoterm_id = fields.Many2one('account.incoterms', string='Incoterm')
    z_invoice = fields.Many2one('account.move', string='Zipper Invoice',readonly=False, store=True)
    m_invoice = fields.Many2one('account.move', string='Metal Trims Invoice',readonly=False, store=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('combine.invoice', sequence_date=seq_date) or _('New')
        
        result = super(CombineInvoice, self).create(vals)
        return result
    
    

class CombineInvoiceLine(models.Model):
    _name = "combine.invoice.line"
    _description = "Customer Invoice Items"
    _check_company_auto = False

    # ==== Business fields ====
    invoice_id = fields.Many2one('combine.invoice', string='Customer Invoice Items',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    # move_id = fields.Many2one('account.move', string='Customer Invoice Items', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    account_move_line = fields.Many2one('account.move.line', string='Move Line', store=True, readonly=True)
    parent_state = fields.Selection(related='invoice_id.state', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one('res.currency', string='Currency')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_id = fields.Many2one('product.product', related='account_move_line.product_id', string='Product Id', ondelete='restrict')
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    # product_id = fields.Many2one('product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Char(string='Item', related='product_template_id.fg_categ_type.name', store=True)
    
    finish = fields.Text(string='Finish', related='sale_order_line.finish', store=True, readonly=True)
    shade = fields.Text(string='Shade', related='sale_order_line.shade', store=True, readonly=True)
    sizcommon = fields.Text(string='Size', store=True, readonly=True, compute='compute_size')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='currency_id')

    


    # @api.depends('sale_order_line.sizein', 'sale_order_line.sizecm', 'sale_order_line.sizemm')
    def compute_size(self):
        for s in self:
            if s.sale_order_line.sizein !=False and s.sale_order_line.sizein != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizein) + ' In' 
            elif s.sale_order_line.sizecm !=False and s.sale_order_line.sizecm != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizecm) + ' Cm'
            elif s.sale_order_line.sizemm !=False and s.sale_order_line.sizemm != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizemm) + ' Mm'




