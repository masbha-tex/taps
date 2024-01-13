from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderwiseRmc(models.Model):
    _name = "sale.orders.rmc"
    _description = "Orders RMC"
    _check_company_auto = True
    #_auto = False
    #_order = "date desc, id desc"
    
    sale_order_lines = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True, check_company=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_lines.order_id', string='OA', readonly=True, store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    payment_term = fields.Many2one('account.payment.term', related='oa_id.payment_term_id', string='Payment Term', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    validity_date = fields.Date(string='Expiration', related='oa_id.validity_date', readonly=True)
    product_id = fields.Many2one( 'product.product', related='sale_order_lines.product_id', string='Product Id', ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one('product.template', string='Product', related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)], store=True)
    fg_categ_type = fields.Char(related='product_template_id.fg_categ_type.name', string='Item', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit', related='product_template_id.uom_id')
    product_uom_qty = fields.Float(string='Quantity', related='sale_order_lines.product_uom_qty', digits='Product Unit of Measure', readonly=True)
    price_unit = fields.Float('Unit Price', related='sale_order_lines.price_unit', digits='Product Price', default=0.0, readonly=True, store=True)

    slidercodesfg = fields.Text(string='Slider', related='sale_order_lines.slidercodesfg', readonly=True)
    sizein = fields.Text(string='Size (Inch)', related='sale_order_lines.sizein', store=True, readonly=True)
    sizecm = fields.Text(string='Size (CM)', related='sale_order_lines.sizecm', store=True, readonly=True)
    sizemm = fields.Text(string='Size (MM)', related='sale_order_lines.sizemm', store=True, readonly=True)
    gap = fields.Text(string='Gap', related='sale_order_lines.gap', readonly=True)
    
    dyedtape = fields.Text(string='Dyed Tape', related='sale_order_lines.dyedtape', readonly=True)
    ptopfinish = fields.Text(string='Top Finish', related='sale_order_lines.ptopfinish', readonly=True)
    numberoftop = fields.Text(string='N.Top', related='sale_order_lines.numberoftop', readonly=True)
    pbotomfinish = fields.Text(string='Bottom Finish', related='sale_order_lines.pbotomfinish', readonly=True)
    ppinboxfinish = fields.Text(string='Pin-Box Finish', related='sale_order_lines.ppinboxfinish', readonly=True)
    dippingfinish = fields.Text(string='Dipping Finish', related='sale_order_lines.dippingfinish', readonly=True)

    logo = fields.Text(string='Logo', related='sale_order_lines.dippingfinish', readonly=True)
    logoref = fields.Text(string='Logo Ref', related='sale_order_lines.dippingfinish', readonly=True)
    logo_type = fields.Text(string='Logo Type', related='sale_order_lines.dippingfinish', readonly=True)
    style = fields.Text(string='Style', related='sale_order_lines.dippingfinish', readonly=True)
    gmt = fields.Text(string='Gmt', related='sale_order_lines.dippingfinish', readonly=True)
    shapefin = fields.Text(string='Shape Finish', related='sale_order_lines.dippingfinish', readonly=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', related='sale_order_lines.dippingfinish', readonly=True)
    b_part = fields.Text(string='B Part', related='sale_order_lines.dippingfinish', readonly=True)
    c_part = fields.Text(string='C Part', related='sale_order_lines.dippingfinish', readonly=True)
    d_part = fields.Text(string='D Part', related='sale_order_lines.dippingfinish', readonly=True)
    finish_ref = fields.Text(string='Finish Ref', related='sale_order_lines.dippingfinish', readonly=True)
    product_code = fields.Text(string='Product Code', related='sale_order_lines.dippingfinish', readonly=True)
    shape = fields.Text(string='Shape', related='sale_order_lines.dippingfinish', readonly=True)
    back_part = fields.Text(string='Back Part', related='sale_order_lines.dippingfinish', readonly=True)
    
    closing_date = fields.Date(string='Closing Date', related='oa_id.closing_date', readonly=False)
    # price_subtotal = fields.Monetary(string='Subtotal', related='sale_order_lines.price_subtotal', store=True)
    currency_id = fields.Many2one('res.currency', related='oa_id.currency_id', string='Currency', readonly=True)
    # currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True, string='Currency', readonly=True)
    price_subtotal = fields.Monetary(related='sale_order_lines.price_subtotal', string='Subtotal', readonly=True, store=True)
    rmc = fields.Float(string='RMC', related='sale_order_lines.rmc', store=True)
    


    def init(self):
        # tools.drop_view_if_exists(self._cr, 'sale_orders_rmc')
        tools.drop_view_if_exists(self._cr, 'sale_orders_rmc')
        
        query = """
        CREATE or REPLACE VIEW sale_orders_rmc AS (select sl.id,sl.id as sale_order_lines,so.id as oa_id from sale_order_line as sl inner join sale_order as so on so.id=sl.order_id where so.sales_type='oa' and so.state='sale' and sl.price_subtotal>0
        )
        """
        self.env.cr.execute(query)