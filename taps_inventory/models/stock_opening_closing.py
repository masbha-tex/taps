import logging
from odoo import fields, models, tools, api, _
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class Inventory(models.Model):
    _name = "stock.opening.closing"
    _description = "Stock Opening & Closing Report"
    #_auto = False
    #_order = "date desc, id desc"
    
    
    product_id = fields.Many2one('product.product', string='Item', readonly=True)
    #product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    product_category = fields.Many2one('category.type', string='Category')
    parent_category = fields.Many2one('category.type', string='Product')
    
    lot_id = fields.Many2one('stock.production.lot', string='Invoice', readonly=True)
    rejected = fields.Boolean(string='Rejected', readonly=True)
    lot_price = fields.Float(string='Price', readonly=True, digits='Unit Price')
    pur_price = fields.Float(string='Pur Price', readonly=True, digits='Unit Price')
    landed_cost = fields.Float(string='Landed Cost', readonly=True, digits='Unit Price')
    opening_qty = fields.Float(string='Opening Quantity', readonly=True)
    opening_value = fields.Float(string='Opening Value', readonly=True)
    receive_qty = fields.Float(string='Receive Quantity', readonly=True)
    receive_value = fields.Float(string='Receive Value', readonly=True)
    issue_qty = fields.Float(string='Issue Quantity', readonly=True)
    issue_value = fields.Float(string='Issue Value', readonly=True)
    cloing_qty = fields.Float(string='Closing Quantity', readonly=True)
    cloing_value = fields.Float(string='Closing Value', readonly=True)
    
    #company_id = fields.Many2one('res.company', readonly=True) 
    
    
    def init(self):
        query = """
        truncate table stock_opening_closing;
        insert into stock_opening_closing(id,product_id,product_category,parent_category,lot_id,rejected,lot_price,pur_price,landed_cost,opening_qty,opening_value,receive_qty,receive_value,issue_qty,issue_value,cloing_qty,cloing_value) select * from (
        select ROW_NUMBER () OVER (ORDER BY product_id) as id, product_id, categ_type as product_category,parent_id as parent_category,invoice as lot_id, rejected, avg(lot_price) as lot_price, avg(pur_price) as pur_price, avg(landed_cost) as landed_cost ,sum(opening_qty) as opening_qty,
        case when avg(lot_price)>0 then sum(opening_qty)*avg(lot_price) else sum(opening_value) end as opening_value,
        sum(receive_qty) as receive_qty,
        case when avg(lot_price)>0 then sum(receive_qty)*avg(lot_price) else sum(receive_value) end as receive_value,
        sum(issue_qty) as issue_qty,
        case when avg(lot_price)>0 then sum(issue_qty)*avg(lot_price) else sum(issue_value) end as issue_value,
        sum(cloing_qty) as cloing_qty,
        case when avg(lot_price)>0 then sum(cloing_qty)*avg(lot_price) else sum(cloing_value) end as cloing_value 
        from(
        select
        product.id as product_id,pt.categ_type,catype.parent_id,lot.id as invoice,lot.rejected,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as lot_price,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as pur_price,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as landed_cost,
        
        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done when a.quantity=0 then 0 else b.qty_done end),0) as op_qty from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<sd.from_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) when a.description like '%LC/%' then a.value else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<sd.from_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_value,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as re_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like '%/IN/%' or a.description like '%/OUT/%') and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like '%/IN/%' or a.description like '%/OUT/%')) end
        ) as receive_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as re_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like '%/IN/%' or a.description like '%/OUT/%') and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like '%/IN/%' or a.description like '%/OUT/%')) end
        ) as receive_value,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as isue_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like '%/MR/%' and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like '%/MR/%') end
        ) as issue_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as re_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like '%/MR/%' and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like '%/MR/%') end
        ) as issue_value,


        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done when a.quantity=0 then 0 else b.qty_done end),0) as op_qty from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) when a.description like '%LC/%' then a.value else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_value

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        left join category_type as pcatype on catype.parent_id=pcatype.id
        left join stock_production_lot as lot on product.id=lot.product_id
        left join searching_date as sd on 1=1
        where product.default_code like'R_%' or product.default_code like'S_%'
        ) as stock where (abs(stock.opening_qty)+abs(stock.receive_qty)+abs(stock.issue_qty))>0
        group by stock.product_id,stock.categ_type,stock.parent_id,stock.invoice,stock.rejected
        ) as atb
        """
        self.env.cr.execute(query)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         for i in range(len(domain)):
#             if domain[i][0] == 'product_tmpl_id' and domain[i][1] in ('=', 'in'):
#                 tmpl = self.env['product.template'].browse(domain[i][2])
#                 # Avoid the subquery done for the related, the postgresql will plan better with the SQL view
#                 # and then improve a lot the performance for the forecasted report of the product template.
#                 domain[i] = ('product_id', 'in', tmpl.with_context(active_test=False).product_variant_ids.ids)
#         return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)