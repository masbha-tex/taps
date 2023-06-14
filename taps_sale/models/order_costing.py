from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderCosting(models.Model):
    _name = "order.costing"
    _auto = False
    _description = "Sale Order Costing"
    
    oa_id = fields.Many2one('sale.order', string='OA')
    so_no = fields.Many2one('sale.order', string='SO')
    pi_number = fields.Char(related='order_id.pi_number',string='PI Number')
    pi_type = fields.Selection(related='order_id.pi_type',string='Type')
    pi_date = fields.Date(related='order_id.pi_date', string='PI Date')
    season = fields.Char(related='order_id.season',string='Season')
    product_category = fields.Char(string='Product')
    product = fields.Char(string='Item')
    slider = fields.Char(string='Slider')
    size = fields.Text(string='Size')
    size_type = fields.Text(string='Size Type')
    
    tape_con = fields.Float('Tape Consumption', digits='Unit Price', default=0.0)
    slider_con = fields.Float('Slider Consumption', digits='Unit Price', default=0.0)
    wire_con = fields.Float('Wire Consumption', digits='Unit Price', default=0.0)
    topwire_con = fields.Float('Topwire Consumption', digits='Unit Price', default=0.0)
    botomwire_con = fields.Float('Botomwire Consumption', digits='Unit Price', default=0.0)
    tbwire_con = fields.Float('TBwire Consumption', digits='Unit Price', default=0.0)
    pinbox_con = fields.Float('Pinbox Consumption', digits='Unit Price', default=0.0)

    tape_price = fields.Float('Tape Price', digits='Unit Price', default=0.0)
    slider_price = fields.Float('Slider Price', digits='Unit Price', default=0.0)
    wire_price = fields.Float('Wire Price', digits='Unit Price', default=0.0)
    topwire_price = fields.Float('Topwire Price', digits='Unit Price', default=0.0)
    botomwire_price = fields.Float('Botomwire Price', digits='Unit Price', default=0.0)
    tbwire_price = fields.Float('TBwire Price', digits='Unit Price', default=0.0)
    pinbox_price = fields.Float('Pinbox Price', digits='Unit Price', default=0.0)

    tape_cost = fields.Float('Tape Cost', digits='Unit Price', default=0.0)
    dyeing_cost = fields.Float('Dyeing Cost', digits='Unit Price', default=0.0)
    slider_cost = fields.Float('Slider Cost', digits='Unit Price', default=0.0)
    wire_cost = fields.Float('Wire Cost', digits='Unit Price', default=0.0)
    depping_cost = fields.Float('Depping Cost', digits='Unit Price', default=0.0)
    topwire_cost = fields.Float('Topwire Cost', digits='Unit Price', default=0.0)
    botomwire_cost = fields.Float('Botomwire Cost', digits='Unit Price', default=0.0)
    tbwire_cost = fields.Float('TBwire Cost', digits='Unit Price', default=0.0)
    pinbox_cost = fields.Float('Pinbox Cost', digits='Unit Price', default=0.0)
    plating_cost = fields.Float('Plating Cost', digits='Unit Price', default=0.0)

    total_cost = fields.Float('Total Cost', digits='Unit Price', default=0.0)
    
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'order_flow')
        
        query = """
        CREATE or REPLACE VIEW order_flow AS (
        select row_number() OVER() AS id,order_id,pi_type,sale_representative,date_order,user_id, 
        pi_number,pi_date,currency_id,partner_id,buyer_name,style_ref,season,po_no,payment_term_id, 
        incoterm,bank,department,product,finish,slider,oa_no, 
        so_qty,so_value,oa_qty,oa_value,quantity_balance,value_balance 
        from
        ( 
        select 
        so.order_id,so.pi_type,so.sale_representative,so.date_order,so.user_id, 
        so.pi_number,so.pi_date,so.currency_id,so.partner_id, 
        so.buyer_name,so.style_ref,so.season,so.po_no,so.payment_term_id, 
        so.incoterm,so.bank,so.department,so.product,so.finish,so.slider,oa.id as oa_no, 
        so.product_uom_qty as so_qty, so.price_subtotal as so_value, oa.product_uom_qty as oa_qty, 
        oa.price_subtotal as oa_value, 
        (so.product_uom_qty-COALESCE(oa.product_uom_qty,0)) as quantity_balance, 
        (so.price_subtotal- COALESCE(oa.price_subtotal,0)) as value_balance 
        from
        (
        select s.id as order_id,s.pi_type,s.sale_representative,s.date_order,s.user_id,
        s.pi_number,s.pi_date,s.currency_id,s.partner_id,s.buyer_name,s.style_ref,s.season,
        s.po_no,s.payment_term_id,s.incoterm,s.bank,s.department,
        pt.name as product,sol.finish,sol.slidercodesfg as slider,
        sum(sol.product_uom_qty) as product_uom_qty,sum(sol.price_subtotal) as price_subtotal
        
        from sale_order as s
        inner join sale_order_line as sol on s.id=sol.order_id 
        inner join product_product as p on p.id = sol.product_id 
        inner join product_template as pt on pt.id = p.product_tmpl_id
        
        where s.state='sale' and s.sales_type in('sale','cancel') and sol.product_uom_qty>0
        group by s.id,s.pi_type,s.sale_representative,
        s.date_order,s.user_id,s.pi_number,s.pi_date, 
        s.currency_id,s.partner_id,s.buyer_name,s.style_ref,
        s.season,s.po_no,s.payment_term_id,s.incoterm,s.bank,s.department,
        pt.name,sol.finish,sol.slidercodesfg
        ) as so
        
        left join
        
        (
        select s.id,s.order_ref,
        pt.name as product,sol.finish,sol.slidercodesfg as slider,
        sum(sol.product_uom_qty) as product_uom_qty,sum(sol.price_subtotal) as price_subtotal
        
        from sale_order as s
        inner join sale_order_line as sol on s.id = sol.order_id 
        inner join product_product as p on p.id = sol.product_id 
        inner join product_template as pt on pt.id = p.product_tmpl_id 
        where s.state='sale' and s.sales_type='oa' and sol.product_uom_qty>0 
        group by s.id,s.order_ref,pt.name,sol.finish,sol.slidercodesfg 
        ) as oa  on so.order_id=oa.order_ref and so.product=oa.product and so.finish=oa.finish and 
        so.slider=oa.slider) as a)
        """
        self.env.cr.execute(query)