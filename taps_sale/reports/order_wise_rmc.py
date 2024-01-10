import logging
from odoo import fields, models, tools, api, _
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderwiseRmc(models.Model):
    _name = "orderwise.rmc"
    _description = "Order wise RMC"
    _check_company_auto = True
    #_auto = False
    #_order = "date desc, id desc"
    
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True, check_company=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', readonly=True, store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    payment_term = fields.Many2one('account.payment.term', related='oa_id.payment_term_id', string='Payment Term', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    validity_date = fields.Date(string='Expiration', related='oa_id.validity_date', readonly=True)
    
    lead_time = fields.Integer(string='Lead Time', compute='get_leadtime', readonly=True)
    
    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Char(related='product_template_id.fg_categ_type.name', string='Item', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit', related='product_template_id.uom_id')
    product_uom_qty = fields.Float(string='Quantity', related='sale_order_line.product_uom_qty', digits='Product Unit of Measure', readonly=True, store=True)
    price_unit = fields.Float('Unit Price', related='sale_order_line.price_unit', digits='Product Price', default=0.0, readonly=True, store=True)
    done_qty = fields.Float(string='Done Qty', digits='Product Unit of Measure', readonly=False, store=True)
    balance_qty = fields.Float(string='Balance', compute='_balance_qty', digits='Product Unit of Measure', readonly=True, group_operator="sum", store=True)

    slidercodesfg = fields.Char(string='Slider', store=True, readonly=True)
    sizein = fields.Char(string='Size (Inch)', store=True, readonly=True)
    sizecm = fields.Char(string='Size (CM)', store=True, readonly=True)
    sizemm = fields.Char(string='Size (MM)', store=True, readonly=True)
    
    dyedtape = fields.Char(string='Dyed Tape', store=True, readonly=True)
    ptopfinish = fields.Char(string='Top Finish', store=True, readonly=True)
    numberoftop = fields.Char(string='N.Top', store=True, readonly=True)
    pbotomfinish = fields.Char(string='Bottom Finish', store=True)
    ppinboxfinish = fields.Char(string='Pin-Box Finish', store=True)
    dippingfinish = fields.Char(string='Dipping Finish', store=True)
    gap = fields.Char(string='Gap', store=True)

    logo = fields.Text(string='Logo', store=True)
    logoref = fields.Text(string='Logo Ref', store=True)
    logo_type = fields.Text(string='Logo Type', store=True)
    style = fields.Text(string='Style', store=True)
    gmt = fields.Text(string='Gmt', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    b_part = fields.Text(string='B Part', store=True)
    c_part = fields.Text(string='C Part', store=True)
    d_part = fields.Text(string='D Part', store=True)
    finish_ref = fields.Text(string='Finish Ref', store=True)
    product_code = fields.Text(string='Product Code', store=True)
    shape = fields.Text(string='Shape', store=True)
    back_part = fields.Text(string='Back Part', store=True)
    
    closing_date = fields.Datetime(string='Closing Date', readonly=False)