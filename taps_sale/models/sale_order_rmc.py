from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class SaleOrderRmc(models.Model):
    _name = "sale.order.rmc"
    _auto = False
    _description = "Sale Order RMC"
    _check_company_auto = True
    
    sale_order_lines = fields.Many2one('sale.order.line', string='Sale Order Line',domain="[('order_id.sales_type', '=', 'oa')]", store=True, check_company=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_lines.order_id', string='OA', readonly=True, store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True, store=True)
    buyer_name = fields.Many2one('res.partner', related='oa_id.buyer_name', string='Buyer', readonly=True, store=True)
    payment_term = fields.Many2one('account.payment.term', related='oa_id.payment_term_id', string='Payment Term', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True, store=True)
    validity_date = fields.Date(string='Expiration', related='oa_id.validity_date', readonly=True)
    product_id = fields.Many2one( 'product.product', related='sale_order_lines.product_id', string='Product Id', ondelete='restrict', check_company=True, store=True)
    product_template_id = fields.Many2one('product.template', string='Product', related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)], store=True)
    fg_categ_type = fields.Char(string='Item', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit', related='product_template_id.uom_id')
    product_uom_qty = fields.Float(string='Quantity', related='sale_order_lines.product_uom_qty', digits='Product Unit of Measure', readonly=True)
    # price_unit = fields.Float('Unit Price', related='sale_order_lines.price_unit', digits='Product Price', readonly=True)

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
    currency_id = fields.Many2one('res.currency', related='oa_id.currency_id', string='Currency', readonly=True)
    price_subtotal = fields.Monetary(related='sale_order_lines.price_subtotal', string='Subtotal', readonly=True, store=True)
    rmc = fields.Float(string='RMC', related='sale_order_lines.rmc', store=True)
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'sale_order_rmc')
        query = """
        CREATE or REPLACE VIEW sale_order_rmc AS (
        select id,sale_order_lines,oa_id,company_id,partner_id,buyer_name,date_order,product_id,product_template_id,fg_categ_type,sizein,sizecm,sizemm,price_subtotal,rmc from (select sl.id, sl.id as sale_order_lines,so.id as oa_id, so.company_id,so.partner_id,so.buyer_name,so.date_order,sl.sizein,sl.sizecm,sl.sizemm,sl.price_subtotal,sl.rmc,p.id as product_id,pt.id as product_template_id, fg.name as fg_categ_type from sale_order_line as sl inner join sale_order as so on so.id=sl.order_id inner join product_product as p on p.id=sl.product_id inner join product_template as pt on p.product_tmpl_id = pt.id inner join fg_category as fg on pt.fg_categ_type=fg.id where so.sales_type='oa' and sl.product_id is not null and so.state='sale' and sl.price_subtotal > 0 and so.company_id=%s and 'a'=%s) as a)"""
        self.env.cr.execute(query,(self.env.company.id,'a'))

    # @api.model
    # def _register_hook(self):
    #     # Create INSTEAD OF UPDATE trigger
    #     self.env.cr.execute("""
    #         CREATE OR REPLACE FUNCTION instead_of_update_sale_order_rmc()
    #         RETURNS TRIGGER AS
    #         $$
    #         BEGIN
    #             -- Your logic to handle the update goes here
    #             -- You may need to update the underlying tables accordingly

    #             RETURN NEW;
    #         END;
    #         $$
    #         LANGUAGE plpgsql;
    #     """)

    #     self.env.cr.execute("""
    #         CREATE TRIGGER instead_of_update_sale_order_rmc
    #         INSTEAD OF UPDATE
    #         ON sale_order_rmc
    #         FOR EACH ROW
    #         EXECUTE FUNCTION instead_of_update_sale_order_rmc();
    #     """)
    #     super(SaleOrderRmc, self)._register_hook()