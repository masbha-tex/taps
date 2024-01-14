from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class SaleOrderRmc(models.Model):
    _name = "sale.order.rmc"
    _auto = False
    _description = "Sale Order RMC"
    _check_company_auto = True
    
    sale_order_lines = fields.Many2one('sale.order.line', string='Sale Order Line', domain="[('order_id.sales_type', '=', 'oa')]", store=True, check_company=True)
    oa_id = fields.Many2one('sale.order', string='OA' , store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company' , store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    partner_id = fields.Many2one('res.partner', string='Customer' , store=True)
    buyer_name = fields.Many2one('res.partner', string='Buyer' , store=True)
    payment_term = fields.Many2one('account.payment.term', string='Payment Term' )
    date_order = fields.Datetime(string='Order Date', store=True)
    validity_date = fields.Date(string='Expiration')
    product_id = fields.Many2one( 'product.product', string='Product Id', ondelete='restrict', check_company=True, store=True)
    product_template_id = fields.Many2one('product.template', string='Product', domain=[('sale_ok', '=', True)], store=True)
    fg_categ_type = fields.Char(string='Item', store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit')
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure' )
    # price_unit = fields.Float('Unit Price', related='sale_order_lines.price_unit', digits='Product Price' )

    slidercodesfg = fields.Text(string='Slider')
    sizein = fields.Text(string='Size (Inch)', store=True )
    sizecm = fields.Text(string='Size (CM)', store=True )
    sizemm = fields.Text(string='Size (MM)', store=True )
    gap = fields.Text(string='Gap')
    
    dyedtape = fields.Text(string='Dyed Tape')
    ptopfinish = fields.Text(string='Top Finish')
    numberoftop = fields.Text(string='N.Top')
    pbotomfinish = fields.Text(string='Bottom Finish')
    ppinboxfinish = fields.Text(string='Pin-Box Finish')
    dippingfinish = fields.Text(string='Dipping Finish')

    # logo = fields.Text(string='Logo', related='sale_order_lines.dippingfinish' )
    # logoref = fields.Text(string='Logo Ref', related='sale_order_lines.dippingfinish' )
    # logo_type = fields.Text(string='Logo Type', related='sale_order_lines.dippingfinish' )
    # style = fields.Text(string='Style', related='sale_order_lines.dippingfinish' )
    # gmt = fields.Text(string='Gmt', related='sale_order_lines.dippingfinish' )
    # shapefin = fields.Text(string='Shape Finish', related='sale_order_lines.dippingfinish' )
    # bcdpart = fields.Text(string='BCD Part Material Type / Size', related='sale_order_lines.dippingfinish' )
    # b_part = fields.Text(string='B Part', related='sale_order_lines.dippingfinish' )
    # c_part = fields.Text(string='C Part', related='sale_order_lines.dippingfinish' )
    # d_part = fields.Text(string='D Part', related='sale_order_lines.dippingfinish' )
    # finish_ref = fields.Text(string='Finish Ref', related='sale_order_lines.dippingfinish' )
    # product_code = fields.Text(string='Product Code', related='sale_order_lines.dippingfinish' )
    # shape = fields.Text(string='Shape', related='sale_order_lines.dippingfinish' )
    # back_part = fields.Text(string='Back Part', related='sale_order_lines.dippingfinish' )
    closing_date = fields.Date(string='Closing Date', readonly=False)
    currency_id = fields.Many2one('res.currency', string='Currency')
    price_subtotal = fields.Monetary(string='Subtotal' , store=True)
    rmc = fields.Float(string='RMC', store=True)
    percent = fields.Float(string='Percent',  store=True, group_operator='avg')#compute="_compute_percent" ,

    # def _compute_percent(self):
    #     for order in self:
    #         if order.price_subtotal > 0 and order.rmc > 0:
    #             order.percent = round(((order.rmc * 100)/order.price_subtotal),2)
    #         else:
    #             order.percent = 0
    

    def init(self):
        tools.drop_view_if_exists(self._cr, 'sale_order_rmc')
        query = """
        CREATE or REPLACE VIEW sale_order_rmc AS (
        select row_number() OVER() AS id ,sale_order_lines,oa_id,company_id,partner_id,buyer_name,payment_term,date_order,validity_date,product_id,product_template_id,fg_categ_type,product_uom,product_uom_qty,slidercodesfg,sizein,sizecm,sizemm,gap,dyedtape,ptopfinish,numberoftop,pbotomfinish,ppinboxfinish,dippingfinish,closing_date,currency_id,price_subtotal,rmc,percent from (select sl.id as sale_order_lines,so.id as oa_id, so.company_id,so.partner_id,so.buyer_name,so.payment_term_id as payment_term,so.date_order,so.validity_date,sl.sizein,sl.sizecm,sl.sizemm,sl.price_subtotal,sl.rmc,p.id as product_id,pt.id as product_template_id, fg.name as fg_categ_type, pt.uom_id as product_uom,sl.product_uom_qty,sl.slidercodesfg,sl.gap,sl.dyedtape,sl.ptopfinish,sl.numberoftop,sl.pbotomfinish,sl.ppinboxfinish,sl.dippingfinish,so.closing_date,so.currency_id,case when sl.price_subtotal > 0 and sl.rmc > 0 then CAST((sl.rmc * 100.0 / sl.price_subtotal) AS numeric(15, 2)) else 0.0 end as percent from sale_order_line as sl inner join sale_order as so on so.id=sl.order_id inner join product_product as p on p.id=sl.product_id inner join product_template as pt on p.product_tmpl_id = pt.id inner join fg_category as fg on pt.fg_categ_type=fg.id where so.sales_type='oa' and sl.product_id is not null and so.state='sale' and sl.price_subtotal > 0 and so.company_id=%s and 'a'=%s) as a)"""
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