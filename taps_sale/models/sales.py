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
    
    @api.depends('product_id', 'name')
    def _compute_topbottom(self):
        for line in self:
            if line.name:
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
    @api.depends('product_id', 'name')
    def _compute_slidercode(self):
        for line in self:
            if line.name:
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
                        
    @api.depends('product_id', 'name')
    def _compute_finish(self):
        for line in self:
            if line.name:
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
                        
    
    @api.depends('product_id', 'name')
    def _compute_shade(self):
        for line in self:
            if line.name:
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
                        
                        
    @api.depends('product_id', 'name')
    def _compute_sizein(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_sizecm(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_sizemm(self):
        for line in self:
            if line.name:
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

    @api.depends('product_id', 'name')
    def _compute_logoref(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_shapefin(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_bcdpart(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_nailmat(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_nailcap(self):
        for line in self:
            if line.name:
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

    @api.depends('product_id', 'name')
    def _compute_fnamebcd(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_nu1washer(self):
        for line in self:
            if line.name:
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
    
    @api.depends('product_id', 'name')
    def _compute_nu2washer(self):
        for line in self:
            if line.name:
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
                        
    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a sale order line. Instead you should delete the current line and create a new line of the proper type."))

        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) != 0)._update_line_quantity(values)

        # Prevent writing on a locked SO.
        protected_fields = self._get_protected_fields()
        if 'done' in self.mapped('order_id.state') and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))
            fields = self.env['ir.model.fields'].search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            raise UserError(
                _('It is forbidden to modify the following fields in a locked order:\n%s')
                % '\n'.join(fields.mapped('field_description'))
            )

        result = super(SaleOrderLine, self).write(values)
        return result

    order_id = fields.Many2one('sale.order', string='Order Reference', required=True, ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
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
    
    sequence = fields.Integer(string='Sequence', default=10)

    invoice_lines = fields.Many2many('account.move.line', 'sale_order_line_invoice_rel', 'order_line_id', 'invoice_line_id', string='Invoice Lines', copy=False)
    invoice_status = fields.Selection([
        ('upselling', 'Upselling Opportunity'),
        ('invoiced', 'Fully Invoiced'),
        ('to invoice', 'To Invoice'),
        ('no', 'Nothing to Invoice')
        ], string='Invoice Status', compute='_compute_invoice_status', store=True, readonly=True, default='no')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)

    price_subtotal = fields.Monetary(compute='_compute_amount', string='Subtotal', readonly=True, store=True)
    price_tax = fields.Float(compute='_compute_amount', string='Total Tax', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)

    price_reduce = fields.Float(compute='_get_price_reduce', string='Price Reduce', digits='Product Price', readonly=True, store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes', domain=['|', ('active', '=', False), ('active', '=', True)])
    price_reduce_taxinc = fields.Monetary(compute='_get_price_reduce_tax', string='Price Reduce Tax inc', readonly=True, store=True)
    price_reduce_taxexcl = fields.Monetary(compute='_get_price_reduce_notax', string='Price Reduce Tax excl', readonly=True, store=True)

    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    product_updatable = fields.Boolean(compute='_compute_product_updatable', string='Can Edit Product', readonly=True, default=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    product_uom_readonly = fields.Boolean(compute='_compute_product_uom_readonly')
    product_custom_attribute_value_ids = fields.One2many('product.attribute.custom.value', 'sale_order_line_id', string="Custom Values", copy=True)

    # M2M holding the values of product.attribute with create_variant field set to 'no_variant'
    # It allows keeping track of the extra_price associated to those attribute values and add them to the SO line description
    product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string="Extra Values", ondelete='restrict')

    qty_delivered_method = fields.Selection([
        ('manual', 'Manual'),
        ('analytic', 'Analytic From Expenses')
    ], string="Method to update delivered qty", compute='_compute_qty_delivered_method', compute_sudo=True, store=True, readonly=True,
        help="According to product configuration, the delivered quantity can be automatically computed by mechanism :\n"
             "  - Manual: the quantity is set manually on the line\n"
             "  - Analytic From expenses: the quantity is the quantity sum from posted expenses\n"
             "  - Timesheet: the quantity is the sum of hours recorded on tasks linked to this sale line\n"
             "  - Stock Moves: the quantity comes from confirmed pickings\n")
    qty_delivered = fields.Float('Delivered Quantity', copy=False, compute='_compute_qty_delivered', inverse='_inverse_qty_delivered', compute_sudo=True, store=True, digits='Product Unit of Measure', default=0.0)
    qty_delivered_manual = fields.Float('Delivered Manually', copy=False, digits='Product Unit of Measure', default=0.0)
    qty_to_invoice = fields.Float(
        compute='_get_to_invoice_qty', string='To Invoice Quantity', store=True, readonly=True,
        digits='Product Unit of Measure')
    qty_invoiced = fields.Float(
        compute='_get_invoice_qty', string='Invoiced Quantity', store=True, readonly=True,
        compute_sudo=True,
        digits='Product Unit of Measure')

    untaxed_amount_invoiced = fields.Monetary("Untaxed Invoiced Amount", compute='_compute_untaxed_amount_invoiced', compute_sudo=True, store=True)
    untaxed_amount_to_invoice = fields.Monetary("Untaxed Amount To Invoice", compute='_compute_untaxed_amount_to_invoice', compute_sudo=True, store=True)

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Analytic Tags',
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    analytic_line_ids = fields.One2many('account.analytic.line', 'so_line', string="Analytic lines")
    is_expense = fields.Boolean('Is expense', help="Is true if the sales order line comes from an expense or a vendor bills")
    is_downpayment = fields.Boolean(
        string="Is a down payment", help="Down payments are made when creating invoices from a sales order."
        " They are not copied when duplicating a sales order.")

    state = fields.Selection(
        related='order_id.state', string='Order Status', readonly=True, copy=False, store=True, default='draft')

    customer_lead = fields.Float(
        'Lead Time', required=True, default=0.0,
        help="Number of days between the order confirmation and the shipping of the products to the customer")

    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

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