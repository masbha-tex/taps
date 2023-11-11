from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderFlow(models.Model):
    _name = "order.flow"
    _auto = False
    _description = "Sale Order Flow"
    _check_company_auto = True
    
    order_id = fields.Many2one('sale.order', string='Sale Orde', store=True)
    company_id = fields.Many2one('res.company', 'Company', index=True, default=lambda self: self.env.company, store=True)
    #name = fields.Char(related='check_id.name',string='Sale Orde')
    # Pi_number = fields.Char(related='check_id.pi_number',string='Pi')
    pi_type = fields.Selection(related='order_id.pi_type',string='Type')
    sale_representative = fields.Many2one(related='order_id.sale_representative',string='Sales')
    date_order = fields.Datetime(related='order_id.date_order',string='Date')
    user_id = fields.Many2one(related='order_id.user_id',string='CSD')
    pi_number = fields.Char(related='order_id.pi_number',string='PI Number')
    pi_date = fields.Date(related='order_id.pi_date', string='PI Date')
    # amount_total = fields.Monetary(related='order_id.amount_total', string='Order Value')
    currency_id = fields.Many2one("res.currency", string="Currency", store=True)
    partner_id = fields.Many2one(related='order_id.partner_id', string='Customer Name')
    buyer_name = fields.Many2one(related='order_id.buyer_name', string='Buyer')
    style_ref = fields.Char(related='order_id.style_ref',string='Style')
    season = fields.Char(related='order_id.season',string='Season')
    po_no = fields.Char(related='order_id.po_no',string='PO No.')
    payment_term_id = fields.Many2one(related='order_id.payment_term_id', string='Payment Term')
    incoterm = fields.Many2one(related='order_id.incoterm', string='Shipment Term')
    bank = fields.Many2one(related='order_id.bank', string='Advised Bank')
    department = fields.Char(related='order_id.department',string='Department')
    
    product = fields.Char(string='Product', store=True)
    finish = fields.Char(string='Finish', store=True)
    slider = fields.Char(string='Slider', store=True)
    oa_no = fields.Char(string='OA', store=True)
    so_qty = fields.Float(string='Order Quantity', store=True)
    so_value = fields.Monetary(string='Order Value', store=True)
    oa_qty = fields.Float(string='OA Quantity', store=True)
    oa_value = fields.Monetary(string='OA Value')
    quantity_balance = fields.Monetary(string='Balance Qty', store=True)
    value_balance = fields.Monetary(string='Balance Value', store=True)
    state = fields.Selection(related='order_id.state',string='Status')
    customer_address = fields.Char(string='Cus. Addr.', compute='_cus_assress')


    def _cus_assress(self):
        for order in self:
            addr = order.partner_id.street
            if order.partner_id.city:
                r_char = addr[-1]
                if r_char == ',':
                    addr = addr + order.partner_id.city
                else:
                    addr = addr + ',' + order.partner_id.city
            if order.partner_id.state_id.name:
                r_char = addr[-1]
                if r_char == ',':
                    addr = addr + order.partner_id.state_id.name
                else:
                    addr = addr + ',' + order.partner_id.state_id.name
            if order.partner_id.country_id.name:
                r_char = addr[-1]
                if r_char == ',':
                    addr = addr + order.partner_id.country_id.name
                else:
                    addr = addr + ',' + order.partner_id.country_id.name
            order.customer_address = addr
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'order_flow')
        
        query = """
        CREATE or REPLACE VIEW order_flow AS (
        select row_number() OVER() AS id,order_id,company_id,pi_type,sale_representative,date_order,user_id, 
        pi_number,pi_date,currency_id,partner_id,buyer_name,style_ref,season,po_no,payment_term_id, 
        incoterm,bank,department,product,finish,slider,oa_no, 
        so_qty,so_value,oa_qty,oa_value,quantity_balance,value_balance,state,'' as customer_address
        from
        ( 
        select 
        so.order_id,so.company_id,so.pi_type,so.sale_representative,so.date_order,so.user_id, 
        so.pi_number,so.pi_date,so.currency_id,so.partner_id, 
        so.buyer_name,so.style_ref,so.season,so.po_no,so.payment_term_id, 
        so.incoterm,so.bank,so.department,so.product,
        
        (select s.finish from sale_order_line as s where s.order_id=so.order_id order by sequence asc limit 1) as finish,
        (select s.slidercodesfg from sale_order_line as s where s.order_id=so.order_id order by sequence asc limit 1) as slider,
        oa.oa_no as oa_no,
        
        so.product_uom_qty as so_qty, so.price_subtotal as so_value, COALESCE(oa.product_uom_qty,0.0) as oa_qty, 
        COALESCE(oa.price_subtotal,0.0) as oa_value,
        so.product_uom_qty-COALESCE(oa.product_uom_qty,0) as quantity_balance,
        so.price_subtotal-COALESCE(oa.price_subtotal,0) as value_balance,
        so.state
        
        from
        (
        select s.id as order_id,s.company_id,s.pi_type,s.sale_representative,s.date_order,s.user_id,
        s.pi_number,s.pi_date,s.currency_id,s.partner_id,s.buyer_name,s.style_ref,s.season,
        s.po_no,s.payment_term_id,s.incoterm,s.bank,s.department,
        pt.name as product,
        sum(sol.product_uom_qty) as product_uom_qty,sum(sol.price_subtotal) as price_subtotal,
        s.state
        from sale_order as s
        inner join sale_order_line as sol on s.id=sol.order_id 
        inner join product_product as p on p.id = sol.product_id 
        inner join product_template as pt on pt.id = p.product_tmpl_id
        
        where  s.company_id=%s and 'a'=%s and s.sales_type='sale' and sol.product_uom_qty>0
        group by s.id,s.company_id,s.pi_type,s.sale_representative,
        s.date_order,s.user_id,s.pi_number,s.pi_date, 
        s.currency_id,s.partner_id,s.buyer_name,s.style_ref,
        s.season,s.po_no,s.payment_term_id,s.incoterm,s.bank,s.department,
        pt.name,s.state
        ) as so
        
        left join
        
        (
        select STRING_AGG(distinct s.name,',') as oa_no,s.company_id,s.order_ref,
        pt.name as product,
        sum(sol.product_uom_qty) as product_uom_qty,sum(sol.price_subtotal) as price_subtotal
        
        from sale_order as s
        inner join sale_order_line as sol on s.id = sol.order_id 
        inner join product_product as p on p.id = sol.product_id 
        inner join product_template as pt on pt.id = p.product_tmpl_id 
        where s.state<>'cancel' and s.sales_type='oa' and sol.product_uom_qty>0 
        group by s.company_id,s.order_ref,pt.name
        ) as oa  on so.order_id=oa.order_ref and so.product=oa.product and so.company_id=oa.company_id) as a 
        order by a.order_id)
        """
        self.env.cr.execute(query,(self.env.company.id,'a'))