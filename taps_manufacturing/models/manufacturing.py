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

SIZE_BACK_ORDER_NUMERING = 3


class SaleOrder(models.Model):
    _name = "manufacturing.order"
    #_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Manufacturing Order"
    #_order = 'date_order desc, id desc'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence')
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', store=True, readonly=True)
    company_id = fields.Many2one(related='oa_id.company_id', string='Company', store=True, readonly=True, index=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    validity_date = fields.Date(string='Expiration', related='oa_id.validity_date', readonly=True)
    
    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product',ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Selection(related='product_template_id.fg_categ_type')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_qty = fields.Float(string='Quantity', related='sale_order_line.product_uom_qty', digits='Product Unit of Measure', readonly=True)
    done_qty = fields.Float(string='Done Quantity', digits='Product Unit of Measure', readonly=True)
    balance_qty = fields.Float(string='Balance Quantity', digits='Product Unit of Measure', readonly=True)
    state = fields.Selection(related='oa_id.state', string='Order Status', readonly=True)

    topbottom = fields.Text(string='Top/Bottom', related='sale_order_line.topbottom', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', related='sale_order_line.slidercodesfg', store=True)
    finish = fields.Text(string='Finish', related='sale_order_line.finish', store=True)
    shade = fields.Text(string='Shade', related='sale_order_line.shade', store=True)
    sizein = fields.Text(string='Size (Inch)', related='sale_order_line.sizein', store=True)
    sizecm = fields.Text(string='Size (CM)', related='sale_order_line.sizecm', store=True)
    sizemm = fields.Text(string='Size (MM)', related='sale_order_line.sizemm', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', related='sale_order_line.dyedtape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', related='sale_order_line.ptopfinish', store=True)
    
    numberoftop = fields.Text(string='Number of Top', related='sale_order_line.numberoftop', store=True)
    
    pbotomfinish = fields.Text(string='Plated Bottom Finish', related='sale_order_line.pbotomfinish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', related='sale_order_line.ppinboxfinish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', related='sale_order_line.dippingfinish', store=True)
    gap = fields.Text(string='Gap', related='sale_order_line.gap', store=True)
    
    logo = fields.Text(string='Logo', related='sale_order_line.logo', store=True)
    logoref = fields.Text(string='Logo Ref', related='sale_order_line.logoref', store=True)
    logo_type = fields.Text(string='Logo Type', related='sale_order_line.logo_type', store=True)
    style = fields.Text(string='Style', related='sale_order_line.style', store=True)
    gmt = fields.Text(string='Gmt', related='sale_order_line.gmt', store=True)
    shapefin = fields.Text(string='Shape Finish', related='sale_order_line.shapefin', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', related='sale_order_line.bcdpart', store=True)
    b_part = fields.Text(string='B Part', related='sale_order_line.b_part', store=True)
    c_part = fields.Text(string='C Part', related='sale_order_line.c_part', store=True)
    d_part = fields.Text(string='D Part', related='sale_order_line.d_part', store=True)
    finish_ref = fields.Text(string='Finish Ref', related='sale_order_line.finish_ref', store=True)
    product_code = fields.Text(string='Product Code', related='sale_order_line.order_id', store=True)
    shape = fields.Text(string='Shape', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    back_part = fields.Text(string='Back Part', store=True)
    
    tape_con = fields.Float('Tape Consumption', readonly=True, digits='Unit Price', store=True)
    slider_con = fields.Float('Slider Consumption', readonly=True, digits='Unit Price', store=True)
    topwire_con = fields.Float('Topwire Consumption', readonly=True, digits='Unit Price', store=True)
    botomwire_con = fields.Float('Botomwire Consumption', readonly=True, digits='Unit Price', store=True)
    tbwire_con = fields.Float('TBwire Consumption', readonly=True, digits='Unit Price', store=True)
    wire_con = fields.Float('Wire Consumption', readonly=True, digits='Unit Price', store=True)
    pinbox_con = fields.Float('Pinbox Consumption', readonly=True, digits='Unit Price', store=True)
    shadewise_tape = fields.Float('Shadwise Tape', readonly=True, digits='Unit Price', store=True, compute='compute_shadewise_tape', compute_sudo=True, store=True)

    dyeing_plan = fields.Date(string='Dyeing Plan', related='oa_id.validity_date', readonly=True)


    

    






    
