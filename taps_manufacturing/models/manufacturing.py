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
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', readonly=True, store=True)
    company_id = fields.Many2one('res.company', related='oa_id.company_id', string='Company', readonly=True, store=True)
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
    #state = fields.Selection(related='oa_id.state', string='Order Status', readonly=True)
    
    topbottom = fields.Text(string='Top/Bottom', compute='_get_line_value', readonly=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', compute='_get_line_value', readonly=True)
    finish = fields.Text(string='Finish', compute='_get_line_value')
    shade = fields.Text(string='Shade', compute='_get_line_value')
    sizein = fields.Text(string='Size (Inch)', compute='_get_line_value')
    sizecm = fields.Text(string='Size (CM)', compute='_get_line_value')
    sizemm = fields.Text(string='Size (MM)', compute='_get_line_value')
    
    dyedtape = fields.Text(string='Dyed Tape', compute='_get_line_value')
    ptopfinish = fields.Text(string='Plated Top Finish', compute='_get_line_value')
    
    numberoftop = fields.Text(string='Number of Top', compute='_get_line_value')
    
    pbotomfinish = fields.Text(string='Plated Bottom Finish', compute='_get_line_value')
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', compute='_get_line_value')
    dippingfinish = fields.Text(string='Dipping Finish', compute='_get_line_value')
    gap = fields.Text(string='Gap', compute='_get_line_value')
    
    logo = fields.Text(string='Logo', compute='_get_line_value')
    logoref = fields.Text(string='Logo Ref', compute='_get_line_value')
    logo_type = fields.Text(string='Logo Type', compute='_get_line_value')
    style = fields.Text(string='Style', compute='_get_line_value')
    gmt = fields.Text(string='Gmt', compute='_get_line_value')
    shapefin = fields.Text(string='Shape Finish', compute='_get_line_value')
    bcdpart = fields.Text(string='BCD Part Material Type / Size', compute='_get_line_value')
    b_part = fields.Text(string='B Part', compute='_get_line_value')
    c_part = fields.Text(string='C Part', compute='_get_line_value')
    d_part = fields.Text(string='D Part', compute='_get_line_value')
    finish_ref = fields.Text(string='Finish Ref', compute='_get_line_value')
    product_code = fields.Text(string='Product Code', compute='_get_line_value')
    shape = fields.Text(string='Shape', compute='_get_line_value')
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', compute='_get_line_value')
    nailcap = fields.Text(string='Nail Cap Logo', compute='_get_line_value')
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', compute='_get_line_value')
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', compute='_get_line_value')
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', compute='_get_line_value')
    back_part = fields.Text(string='Back Part', compute='_get_line_value')
    
    tape_con = fields.Float('Tape Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    slider_con = fields.Float('Slider Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    topwire_con = fields.Float('Topwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    botomwire_con = fields.Float('Botomwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    tbwire_con = fields.Float('TBwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    wire_con = fields.Float('Wire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    pinbox_con = fields.Float('Pinbox Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    shadewise_tape = fields.Float('Shadwise Tape', compute='_get_line_value', readonly=True, digits='Unit Price')

    dyeing_plan = fields.Date(string='Dyeing Plan')
    dyeing_plan_end = fields.Date(string='Dyeing Plan')
    dyeing_plan_qty = fields.Float(string='Dyeing Plan Qty')
    dyeing_output = fields.Float(string='Dyeing Output')
    dyeing_qc_pass = fields.Float(string='Dyeing QC Pass')

    plating_plan = fields.Date(string='Plating Plan')
    plating_plan_end = fields.Date(string='Plating Plan')
    plating_plan_qty = fields.Float(string='Plating Plan Qty')
    plating_output = fields.Float(string='Plating Output')
    plating_qc_pass = fields.Float(string='Plating QC Pass')

    painting_done = fields.Float(string='painting Output')
    
    chain_making_done = fields.Float(string='CM Output')
    diping_done = fields.Float(string='Dipping Output')
    assembly_done = fields.Float(string='Assembly Output')
    packing_done = fields.Float(string='Packing Output')


    def _get_line_value(self):
        self.slidercodesfg = self.sale_order_line.slidercodesfg
        self.finish = self.sale_order_line.finish
        self.shade = self.sale_order_line.shade
        self.sizein = self.sale_order_line.sizein
        self.sizecm = self.sale_order_line.sizecm
        self.sizemm = self.sale_order_line.sizemm
        self.dyedtape = self.sale_order_line.dyedtape
        self.ptopfinish = self.sale_order_line.ptopfinish
        self.numberoftop = self.sale_order_line.numberoftop
        self.pbotomfinish = self.sale_order_line.pbotomfinish
        self.ppinboxfinish = self.sale_order_line.ppinboxfinish
        self.dippingfinish = self.sale_order_line.dippingfinish
        self.gap = self.sale_order_line.gap
        self.logo = self.sale_order_line.logo
        self.logoref = self.sale_order_line.logoref
        self.logo_type = self.sale_order_line.logo_type
        self.style = self.sale_order_line.style
        self.gmt = self.sale_order_line.gmt
        self.shapefin = self.sale_order_line.shapefin
        self.bcdpart = self.sale_order_line.bcdpart
        self.b_part = self.sale_order_line.b_part
        self.c_part = self.sale_order_line.c_part
        self.d_part = self.sale_order_line.d_part
        self.finish_ref = self.sale_order_line.finish_ref
        self.product_code = self.sale_order_line.product_code
        self.shape = self.sale_order_line.shape
        self.nailmat = self.sale_order_line.nailmat
        self.nailcap = self.sale_order_line.nailcap
        self.fnamebcd = self.sale_order_line.fnamebcd
        self.nu1washer = self.sale_order_line.nu1washer
        self.nu2washer = self.sale_order_line.nu2washer
        self.back_part = self.sale_order_line.back_part
        

    def button_plan(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

    def button_requisition(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action
    
    def button_createlot(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

    def button_output(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

