from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderFlow(models.Model):
    _name = "order.flow"
    _auto = False
    _description = "Sale Order Flow"
    
    order_id = fields.Many2one('sale.order', string='Sale Orde')
    #name = fields.Char(related='check_id.name',string='Sale Orde')
    # Pi_number = fields.Char(related='check_id.pi_number',string='Pi')
    pi_type = fields.Selection(related='order_id.pi_type',string='Type')
    sale_representative = fields.Many2one(related='order_id.sale_representative',string='Sales')
    date_order = fields.Datetime(related='order_id.date_order',string='Date')
    user_id = fields.Many2one(related='order_id.user_id',string='CSD')
    pi_number = fields.Char(related='order_id.pi_number',string='PI Number')
    pi_date = fields.Date(related='order_id.pi_date', string='PI Date')
    # amount_total = fields.Monetary(related='order_id.amount_total', string='Order Value')
    currency_id = fields.Many2one("res.currency", string="Currency")
    partner_id = fields.Many2one(related='order_id.partner_id', string='Customer Name')
    buyer_name = fields.Many2one(related='order_id.buyer_name', string='Buyer')
    style_ref = fields.Char(related='order_id.style_ref',string='Style')
    season = fields.Char(related='order_id.season',string='Season')
    po_no = fields.Char(related='order_id.po_no',string='PO No.')
    payment_term_id = fields.Many2one(related='order_id.payment_term_id', string='Payment Term')
    incoterm = fields.Many2one(related='order_id.incoterm', string='Shipment Term')
    bank = fields.Many2one(related='order_id.bank', string='Advised Bank')
    department = fields.Char(related='order_id.department',string='Department')
    product = fields.Char(string='Product')
    finish = fields.Char(string='Finish')
    slider = fields.Char(string='Slider')
    oa_no = fields.Many2one('sale.order', string='OA')
    so_qty = fields.Float(string='Order Quantity')
    so_value = fields.Monetary(string='Order Value')
    oa_qty = fields.Float(string='OA Quantity')
    oa_value = fields.Monetary(string='OA Value')
    quantity_balance = fields.Monetary(string='Balance Qty')
    value_balance = fields.Monetary(string='Balance Value')
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'order_flow')
        
        query = """
        CREATE or REPLACE VIEW order_flow AS (
        select row_number() OVER() AS id,order_id,pi_type,sale_representative,date_order,user_id,
        pi_number,pi_date,currency_id,partner_id,buyer_name,style_ref,season,po_no,payment_term_id,
        incoterm,bank,department,product,finish,slider,oa_no,
        
        sum(product_uom_qty) as so_qty,
        sum(price_subtotal) as so_value,
        sum(oa_qty) as oa_qty,
        sum(oa_value) as oa_value,
        
        (sum(product_uom_qty)-sum(oa_qty)) as quantity_balance,
        (sum(price_subtotal)-sum(oa_value)) as value_balance
        
        
        from
        (
        select s.id as order_id,s.pi_type,s.sale_representative,s.date_order,s.user_id,s.pi_number,s.pi_date,
        s.currency_id,s.partner_id,s.buyer_name,s.style_ref,
        s.season,s.po_no,s.payment_term_id,s.incoterm,s.bank,s.department,
        
        pt.name as product,
        sol.finish,
        sol.slidercodesfg as slider,
        oa.id as oa_no,
        sol.product_uom_qty,
        sol.price_subtotal,
        
        COALESCE((select sum(oa_l.product_uom_qty)  from sale_order_line as oa_l where oa_l.order_id=oa.id 
        and oa_l.product_id=sol.product_id and oa_l.finish=sol.finish and oa_l.slidercodesfg=sol.slidercodesfg),0)
        as oa_qty,
        
        COALESCE((select sum(oa_l.price_subtotal) from sale_order_line as oa_l where oa_l.order_id=oa.id 
        and oa_l.product_id=sol.product_id and oa_l.finish=sol.finish and oa_l.slidercodesfg=sol.slidercodesfg),0)
        as oa_value

        from sale_order as s
        inner join sale_order_line as sol on s.id=sol.order_id
        
        inner join product_product as p on p.id=sol.product_id
        inner join product_template as pt on pt.id=p.product_tmpl_id
        
        left join sale_order as oa on oa.order_ref=s.id
        
        where s.state='sale' and s.sales_type='sale'
        ) as all_so group by order_id,pi_type,sale_representative,date_order,user_id,
        pi_number,pi_date,currency_id,partner_id,buyer_name,style_ref,season,po_no,payment_term_id,
        incoterm,bank,department,product,finish,slider,oa_no order by order_id,product,finish,slider,oa_no)
        """
        self.env.cr.execute(query)