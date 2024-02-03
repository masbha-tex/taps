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
    _description = "Customer Invoice"
    _check_company_auto = True

    # ==== Business fields ====
    name = fields.Char(string='Number', copy=False, readonly=False, store=True, index=True, tracking=True)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, tracking=True, required=True,
        states={'draft': [('readonly', False)]},
        string='Currency',
        default=_get_default_currency)
    line_ids = fields.One2many('combine.invoice.line', 'invoice_id', string='Customer Invoice Items', copy=True, readonly=True,
        states={'draft': [('readonly', False)]})
    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
        states={'draft': [('readonly', False)]},
        check_company=True,
        string='Partner', change_default=True, ondelete='restrict')
    # commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', store=True, readonly=True,
    #     compute='_compute_commercial_partner_id', ondelete='restrict')
    # country_code = fields.Char(related='company_id.country_id.code', readonly=True)
    # user_id = fields.Many2one(string='User', related='invoice_user_id',
    #     help='Technical field used to fit the generic behavior in mail templates.')
    
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank',
        compute="_compute_partner_bank_id", store=True, readonly=False,
        help='Bank Account Number to which the invoice will be paid. A Company bank account if this is a Customer Invoice or Vendor Credit Note, otherwise a Partner bank account number.',
        check_company=True)
    payment_reference = fields.Char(string='Payment Reference', index=True, copy=False,
        compute='_compute_payment_reference', store=True, readonly=False,
        help="The payment reference to set on journal items.")
    
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,
        states={'draft': [('readonly', False)]})
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        check_company=True,
        readonly=True, states={'draft': [('readonly', False)]})
    # /!\ invoice_line_ids is just a subset of line_ids.
    invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',
        copy=False, readonly=True,
        domain=[('exclude_from_invoice_tab', '=', False)],
        states={'draft': [('readonly', False)]})
    invoice_incoterm_id = fields.Many2one('account.incoterms', string='Incoterm',
        default=_get_default_invoice_incoterm,
        help='International Commercial Terms are a series of predefined commercial terms used in international transactions.')
    z_invoice = fields.Many2one('account.move', string='Zipper Invoice',readonly=True, store=True)
    m_invoice = fields.Many2one('account.move', string='Metal Trims Invoice',readonly=True, store=True)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    
    

class CombineInvoiceLine(models.Model):
    _name = "combine.invoice.line"
    _description = "Customer Invoice Items"
    _check_company_auto = True

    # ==== Business fields ====
    invoice_id = fields.Many2one('combine.invoice', string='Customer Invoice Items',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    account_move_line = fields.Many2one('account.move.line', string='Sale Order Line', store=True, readonly=True)
    parent_state = fields.Selection(related='move_id.state', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict')
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')


    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Char(related='product_template_id.fg_categ_type.name', string='Item', store=True)
    
    
    finish = fields.Char(string='Finish', store=True, readonly=True)
    shade = fields.Char(string='Shade', store=True, readonly=True)
    sizcommon = fields.Char(string='Size (In/Cm/Mm)', store=True, readonly=True, compute='compute_size')
    quantity = fields.Float(string='Quantity',
        default=lambda self: 0 if self._context.get('default_display_type') else 1.0, digits='Product Unit of Measure',
        help="The optional quantity expressed by this line, eg: number of product sold. "
             "The quantity is not a legal requirement but is very useful for some reports.")
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='currency_id')




