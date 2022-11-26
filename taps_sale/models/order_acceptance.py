from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare



from werkzeug.urls import url_encode

class OrderAcceptance(models.Model):
    _name = "order.acceptance"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Order Acceptance"
    _order = 'oa_date desc, id desc'
    _check_company_auto = True
    
    #id, product_id, name, unit
    name = fields.Char(string='OA Number', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default=lambda self: _('New'))
    sale_order = fields.Many2one('sale.order', string='Sales Order', readonly=True, states={'draft': [('readonly', False)]})
    oa_date = fields.Datetime(string='OA Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now, help="Creation date of OA")
    delivery_date = fields.Datetime(string='Delivery Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    priority = fields.Selection([
        ('first', 'Top Priority'),
        ('second', 'Regular'),
        ('third', 'No'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    state = fields.Selection([
        ('draft', 'OA Generation'),
        ('done', 'Confirm OA'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=3, default='draft')
    oa_line = fields.One2many('order.acceptance.line', 'oa_id', string='OA Lines', states={'cancel': [('readonly', True)], 'done': [('readonly', True)]}, copy=True, auto_join=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    
    
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'oa_date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['oa_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('order.acceptance', sequence_date=seq_date) or _('New')
        result = super(OrderAcceptance, self).create(vals)
        return result
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        #if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
        #    partner = self.env['res.partner'].browse(vals.get('partner_id'))
        #    addr = partner.address_get(['delivery', 'invoice'])
        #    vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
        #    vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
        #    vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist.id)
        #result = super(SaleOrder, self).create(vals)
        
        
    @api.onchange('sale_order')
    def onchange_sale_order(self):
        """
        Update the OA lines when the Sale Order is changed
        """
        if not self.sale_order:
            return
        saleorder_products = self.env['sale.order.line'].search([('order_id','=',self.sale_order.id)], order='sequence')
        for lines in saleorder_products:
            remaining_qty = lines.product_uom_qty
            oa_products = self.env['order.acceptance.line'].search([('saleorder_lines','=',lines.id),('state','in',('draft','done'))])
            if oa_products:
                remaining_qty -= sum(oa_products.mapped('product_uom_qty'))
            if remaining_qty>0:
                lines.oa_line.create({'oa_id':self.id,
                                      'sequence':lines.sequence,
                                      'saleorder_lines':lines.saleorder_lines,
                                      'state':lines.state,
                                      'product_id':lines.product_id.id,
                                      'product_template_id':lines.product_template_id.id,
                                      'remaining_qty':remaining_qty,
                                      'product_qty':0.0,
                                      'product_uom':lines.product_uom.id,
                                      'topbottom':lines.topbottom,
                                      'slidercode':lines.slidercode,
                                      'slidercodesfg':lines.slidercodesfg,
                                      'finish':lines.finish,
                                      'shade':lines.shade,
                                      'sizein':lines.sizein,
                                      'sizecm':lines.sizecm,
                                      'sizemm':lines.sizemm,
                                      'dyedtape':lines.dyedtape,
                                      'ptopfinish':lines.ptopfinish,
                                      'pbotomfinish':lines.pbotomfinish,
                                      'ppinboxfinish':lines.ppinboxfinish,
                                      'dippingfinish':lines.dippingfinish,
                                      'gap':lines.gap,
                                      'logoref':lines.logoref,
                                      'shapefin':lines.shapefin,
                                      'bcdpart':lines.bcdpart,
                                      'nailmat':lines.nailmat,
                                      'nailcap':lines.nailcap,
                                      'fnamebcd':lines.fnamebcd,
                                      'nu1washer':lines.nu1washer,
                                      'nu2washer':lines.nu2washer,
                                      'bom_id':lines.bom_id,
                                     })
    def action_confirm(self):
        for products in self.saleorder_lines:
            self.env['mrp.production'].create({
                'priority': self.product_id.id,
                'product_id': products.product_id.id,
                'product_qty': products.product_qty,
                'product_uom_id': products.product_uom.id,
                'qty_producing': 0,
                'product_uom_qty': products.product_qty,
                'picking_type_id': 8,
                'location_src_id': 8,
                'location_dest_id': 8,
                'date_planned_start': datetime.datetime.now(),
                'date_planned_finished': datetime.datetime.now() + datetime.timedelta(hours=1),
                'bom_id': products.bom_id,
                'state': 'draft',
                #'user_id': self.company_id.id,
                'company_id': self.company_id.id,
                'procurement_group_id': self.company_id.id,
                'propagate_cancel': False,
                'is_locked': False,
                'production_location_id': 15,
                'consumption': 'warning'
            })
        
        
class OrderAcceptanceLine(models.Model):
    _name = 'order.acceptance.line'
    _description = 'OA Line'
    _order = 'oa_id, sequence, id'
    
    
    oa_id = fields.Many2one('order.acceptance', string='OA Reference', required=True, ondelete='cascade', index=True, copy=False)
    sequence = fields.Integer(string='Sequence', default=10)

    saleorder_lines = fields.Many2many('sale.order.line', string='Order Lines', copy=False)
    state = fields.Selection(related='oa_id.state', store=True, readonly=False)

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    remaining_qty = fields.Float(string='Remaining', digits='Product Unit of Measure')
    product_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=0.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    
    topbottom = fields.Text(string='Top/Bottom', store=True)
    slidercode = fields.Text(string='Slider Code', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    sizemm = fields.Text(string='Size (MM)', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', store=True)
    pbotomfinish = fields.Text(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', store=True)
    gap = fields.Text(string='Gap', store=True)
    
    logoref = fields.Text(string='Logo & Ref', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    bom_id = fields.Integer('Bom Id')
    
    #@api.depends('product_id', 'oa_id.sale_order')
    #def _compute_remaining_qty(self):
    #    for oaline in self:  