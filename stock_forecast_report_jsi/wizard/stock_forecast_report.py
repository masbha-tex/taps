import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models
import math
_logger = logging.getLogger(__name__)


class StockForecastReport(models.TransientModel):
    _name = 'stock.forecast.report'
    _description = 'Bridge Report'
    _check_company_auto = True

    report_type = fields.Selection([
        ('rmstock', 'RM Stock'),
        ('rmstockwithzero', 'RM Stock (with 0)'),
        ('rmc', 'RM Consumption'),
        ('ageing', 'Stock Ageing'),
        ('ppcom', 'Product Price Comparison')], 
        default='rmstock', string='Report Type')
    
    report_for = fields.Selection([
        ('rm', 'RM'),
        ('spare', 'Spare Parts')], 
        default='rm', string='Report For')
    
#     report_by = fields.Selection([
#         ('by_categories', 'By Categories'),
#         ('by_items', 'By Items')], 
#         default='by_categories')
#     categ_ids = fields.Many2many('category.type', string='Categories')
#     product_ids = fields.Many2many('product.product')
    
    from_date = fields.Date('From')
    to_date = fields.Date('To', default=fields.Date.context_today)
    file_data = fields.Binary(readonly=True, attachment=False)
#     is_spare = fields.Boolean(string='Is a RM', default=False,
#         help="Check if the product is a RM, otherwise it is a Spare Parts")
#     stock_type = fields.Selection(string='Stock of',
#                                     selection=[('rm', 'RM'), ('spare', 'Spare Parts')],
#                                   compute='_compute_stock_type', inverse='_write_stock_type')
#     # report_type = fields.Boolean(readonly=False, default=False)  
#     company_id = fields.Many2one('res.company', 'Company', readonly=True, default=lambda self: self.env.company.id)
    
#     @api.depends('is_spare')
#     def _compute_stock_type(self):
#         for stock in self:
#             stock.stock_type = 'spare' if stock.is_spare else 'rm'

#     def _write_stock_type(self):
#         for stock in self:
#             stock.is_spare = stock.stock_type == 'spare'

#     @api.onchange('stock_type')
#     def onchange_company_type(self):
#         self.is_spare = (self.stock_type == 'spare')
        
    def getopening_qty(self,productid,fr_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', fr_date)])
        qty = sum(stock_details.mapped('quantity'))
        
        
        #query = """select * from stock SET store_fname='""" + fn + """', file_size=%s,checksum='""" + cm + """' where res_model='hr.expense.sheet' and res_id=%s"""
        #cr = self._cr
        #cr.execute(query, (fs, sheet.id))
        
        
        
        #mobile_records = cursor.fetchall()
        
        
        return qty
    
    def getopening_val(self,productid,from_date):
        prev_date = datetime.strptime('2022-04-01', '%Y-%m-%d')
        if from_date>prev_date:
            stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', prev_date)])#,('description','not like','%LC/%')
            val = sum(stock_details.mapped('value'))
            stock_details_wolc = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', from_date),('schedule_date', '>=', prev_date),('description','not like','%LC/%')])#
            val = val + sum(stock_details_wolc.mapped('value'))
            
            landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', prev_date),('date', '<', from_date.date())])

            lclist = landedcost.mapped('id')
            lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
            lc_val = 0
            if len(lc_details)>0:
                lc_val = sum(lc_details.mapped('additional_landed_cost'))
                val = val + lc_val
        else:
            stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', from_date)])#,('description','not like','%LC/%')
            val = sum(stock_details.mapped('value'))
#         landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '<', from_date.date())])
        
#         lclist = landedcost.mapped('id')
#         lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
#         lc_val = 0
#         if len(lc_details)>0:
#            lc_val = sum(lc_details.mapped('additional_landed_cost'))
#            val = val + lc_val
        return val
    
    def getreceive_qty(self,productid,from_date,to_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid)
                                                                  ,('schedule_date', '>=', from_date),
                                                                  ('schedule_date', '<=', to_date),
                                                                  '|',
                                                                  ('description','like','%/IN/%')
                                                                  ,('description','like','%/OUT/%')
                                                                 ])
        
        #,('quantity', '>=', 0),('description','not like','%Product Quantity Updated%'),('description','not like','%/MR/%')
        qty = sum(stock_details.mapped('quantity'))
        return qty
    
    def getreceive_val(self,productid,from_date,to_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),
                                                                  ('schedule_date', '>=', from_date),
                                                                  ('schedule_date', '<=', to_date),
                                                                  '|',
                                                                  ('description','like','%/IN/%')
                                                                  ,('description','like','%/OUT/%')
                                                                 ])
        val = sum(stock_details.mapped('value'))
        
        landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', from_date.date()),('date', '<=', to_date.date())])
        
        lclist = landedcost.mapped('id')
        lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
        lc_val = 0
        if len(lc_details)>0:
            lc_val = sum(lc_details.mapped('additional_landed_cost'))
            val = val + lc_val
        return val
    
    def getissue_qty(self,productid,from_date,to_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '>=', from_date),('schedule_date', '<=', to_date),('description','like','%/MR/%')])#,('description','not like','%Product Quantity Updated%') #('quantity', '<', 0),
        qty = sum(stock_details.mapped('quantity'))
        return qty
    
    def getissue_val(self,productid,from_date,to_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '>=', from_date),('schedule_date', '<=', to_date),('description','like','%/MR/%')])#,('description','not like','%Product Quantity Updated%') #('quantity', '<', 0),
        val = sum(stock_details.mapped('value'))
        return val

    def getclosing_qty(self,productid,to_date):
        stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<=', to_date)])
        qty = sum(stock_details.mapped('quantity'))
        return qty
    
    def getclosing_val(self,productid,to_date):
        prev_date = datetime.strptime('2022-04-01', '%Y-%m-%d')
        if to_date>prev_date:
            stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', prev_date)])#,('description','not like','%LC/%')
            val = sum(stock_details.mapped('value'))
            stock_details_wolc = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<=', to_date),('schedule_date', '>=', prev_date),('description','not like','%LC/%')])#
            val = val + sum(stock_details_wolc.mapped('value'))
            
            landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', prev_date),('date', '<=', to_date.date())])

            lclist = landedcost.mapped('id')
            lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
            lc_val = 0
            if len(lc_details)>0:
                lc_val = sum(lc_details.mapped('additional_landed_cost'))
                val = val + lc_val
        
        else:
            stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<=', to_date)])
            #,('description','not like','%LC/%')
            val = sum(stock_details.mapped('value'))
        return val
        #landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '<', to_date.date())])
        
        #lclist = landedcost.mapped('id')
        #lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
        #lc_val = 0
        #if len(lc_details)>0:
        #    lc_val = sum(lc_details.mapped('additional_landed_cost'))
        #    val = val + lc_val
        
    def float_to_time(self,hours):
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(round(60 * fractional, precision_digits=0)), 0)    
    
    def print_date_wise_stock_register(self):
        start_time = fields.datetime.now()
        f_date = self.to_date
        if self.from_date:
            f_date = self.from_date
        t_date = self.to_date
        hour_from = 0.0
        hour_to = 23.98
        combine = datetime.combine
        from_date = combine(f_date, self.float_to_time(hour_from))
        to_date = combine(t_date, self.float_to_time(hour_to))
        to_date = to_date.replace(second=59)
        if self.report_type == 'rmstock':
            #search_date = self.env['searching.date'].search([('id','=',1)])
            #search_date.write({'from_date':from_date,'to_date':to_date})
            self.get_opening_closing(from_date,to_date)
            vewid = self.env['ir.ui.view'].search([('model', '=', 'stock.opening.closing'), ('type', '=', 'list')])
            if (self.report_for == 'rm'):
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.opening.closing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_rm_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }
            else:
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.opening.closing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_spare_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }
        if self.report_type == 'ppcom':
            self.get_price_comparison(from_date,to_date)
            vewid = self.env['ir.ui.view'].search([('model', '=', 'product.price.comparison'), ('type', '=', 'list')])
            return {
                'view_mode': 'list',
                'view_id': vewid,
                'view_type': 'list',
                'res_model': 'product.price.comparison',
                'type': 'ir.actions.act_window',
                'target': 'self',
                'context': {'search_default_comparison_group':1}
            }
        if self.report_type == 'rmstockwithzero':
            #search_date = self.env['searching.date'].search([('id','=',1)])
            #search_date.write({'from_date':from_date,'to_date':to_date})
            self.get_opening_closing_withzero(from_date,to_date)
            vewid = self.env['ir.ui.view'].search([('model', '=', 'stock.opening.closing'), ('type', '=', 'list')])
            if (self.report_for == 'rm'):
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.opening.closing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_rm_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }
            else:
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.opening.closing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_spare_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }
                
        if self.report_type == 'rmc':
            raise UserError(('This report is under construction'))
            
        if self.report_type == 'ageing':
            #search_date = self.env['searching.date'].search([('id','=',1)])
            #search_date.write({'from_date':from_date,'to_date':to_date})
            self.get_ageing(to_date)
            vewid = self.env['ir.ui.view'].search([('model', '=', 'stock.ageing'), ('type', '=', 'list')])
            if (self.report_for == 'rm'):
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.ageing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_rm_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }
            else:
                return {
                    #'name':'Stock Register',#Name You want to display on wizard
                    'view_mode': 'list',
                    'view_id': vewid,
                    'view_type': 'list',
                    'res_model': 'stock.ageing',# With . Example sale.order
                    'type': 'ir.actions.act_window',
                    'target': 'self',
                    'context': {'search_default_spare_stock':1, 'search_default_product_group':1, 'search_default_category_group':1, 'search_default_item_group':1}
                }

        # (select x_studio_shipment_mode from purchase_order where name in(select origin from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product_id and sl.lot_id=invoice and sl.state='done' and sl.reference like %s order by sl.picking_id asc) order by id limit 1)) as shipment_mode,

        # (select po_type from purchase_order where name in(select origin from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product_id and sl.lot_id=invoice and sl.state='done' and sl.reference like %s order by sl.picking_id asc) order by id limit 1)) as po_type
        
    def get_opening_closing(self,from_date,to_date):
        
        query_ = """truncate table stock_opening_closing; update searching_date set from_date=%s,
        to_date=%s;"""
        self.env.cr.execute(query_,(from_date,to_date))
        
        
        query = """
        insert into stock_opening_closing(id,product_id,pr_code,product_category,parent_category,lot_id,rejected,lot_price,pur_price,landed_cost,opening_qty,opening_value,receive_date,receive_qty,receive_value,issue_qty,issue_value,cloing_qty,cloing_value,shipment_mode,po_type) select * from (
        select ROW_NUMBER () OVER (ORDER BY product_id) as id, product_id,pr_code,categ_type as product_category,parent_id as parent_category,invoice as lot_id, case when rejected=true then 'Reject' else 'Ok' end as rejected, avg(lot_price) as lot_price, avg(pur_price) as pur_price, avg(landed_cost) as landed_cost ,sum(opening_qty) as opening_qty,
        case when avg(lot_price)>0 then sum(opening_qty)*avg(lot_price) else sum(opening_value) end as opening_value,
        
        min(COALESCE(date(receive_date),'2021-01-01')) as receive_date,
        
        sum(receive_qty) as receive_qty,
        case when avg(lot_price)>0 then sum(receive_qty)*avg(lot_price) else sum(receive_value) end as receive_value,
        sum(issue_qty) as issue_qty,
        case when avg(lot_price)>0 then sum(issue_qty)*avg(lot_price) else sum(issue_value) end as issue_value,
        sum(cloing_qty) as cloing_qty,
        case when avg(lot_price)>0 then sum(cloing_qty)*avg(lot_price) else sum(cloing_value) end as cloing_value,
        (select x_studio_shipment_mode from purchase_order where name=stock.po_number) as shipment_mode,
        (select po_type from purchase_order where name=stock.po_number) as po_type
        
        from(
        select
        product.id as product_id,product.default_code as pr_code,pt.categ_type,catype.parent_id,lot.id as invoice,lot.rejected,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as lot_price,
        
        (case when lot.id is not null then
        lot.pur_price else 0 end
        ) as pur_price,
        
        (case when lot.id is not null then
        lot.landed_cost else 0 end
        ) as landed_cost,
        
        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as op_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_qty,

        (
        case when lot.id is not null then
		(select (sum(op_qty)*avg(cost))+sum(lc_cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as op_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost, COALESCE((select sum(l.value) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id and l.description like %s),0) as lc_cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_value,
        
        
        (select min(scheduled_date) from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product.id and sl.lot_id=lot.id and sl.state='done' and sl.reference like %s order by sl.picking_id asc)) as receive_date,
        
        (select origin from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product.id and sl.lot_id=lot.id and sl.state='done' and sl.reference like %s order by sl.picking_id asc) order by scheduled_date asc limit 1) as po_number,

        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as re_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where (a.description like %s or a.description like %s) and a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like %s or a.description like %s)) end
        ) as receive_qty,

        (
        case when lot.id is not null then
		(select sum(re_qty)*avg(cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as re_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where (a.description like %s or a.description like %s) and a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like %s or a.description 
        like %s)) end
        ) as receive_value,

        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as iss_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.description like %s and a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like %s) end
        ) as issue_qty,

        (
        case when lot.id is not null then
		(select sum(iss_qty)*avg(cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as iss_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.description like %s and a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like %s) end
        ) as issue_value,


        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_qty,

        (
        case when lot.id is not null then
		(select (sum(cl_qty)*avg(cost))+sum(lc_cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost, COALESCE((select sum(l.value) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id and l.description like %s),0) as lc_cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date and a.schedule_date<=sd.to_date) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_value,
        
        pt.company_id

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        left join category_type as pcatype on catype.parent_id=pcatype.id
        left join stock_production_lot as lot on product.id=lot.product_id
        left join searching_date as sd on 1=1
        where pt.company_id = %s and (product.default_code like %s or product.default_code like %s)
        ) as stock where (abs(stock.opening_qty)+abs(stock.receive_qty)+abs(stock.issue_qty))>0
        group by stock.product_id,stock.pr_code,stock.categ_type,stock.parent_id,stock.invoice,stock.rejected,stock.company_id,stock.po_number
        ) as atb
        """
        self.env.cr.execute(query, ('%LC/%','%/IN/%','%/IN/%','%/IN/%','%/OUT/%','%/IN/%','%/OUT/%','%/IN/%','%/OUT/%','%/IN/%','%/OUT/%','%/MR/%','%/MR/%','%/MR/%','%/MR/%','%LC/%',self.env.company.id,'R_%','S_%'))
        
        
    def get_opening_closing_withzero(self,from_date,to_date):
        
        query_ = """truncate table stock_opening_closing; update searching_date set from_date=%s,
        to_date=%s;"""
        self.env.cr.execute(query_,(from_date,to_date))
        
        
        query = """
        insert into stock_opening_closing(id,product_id,pr_code,product_category,parent_category,lot_id,rejected,lot_price,pur_price,landed_cost,opening_qty,opening_value,receive_date,receive_qty,receive_value,issue_qty,issue_value,cloing_qty,cloing_value,shipment_mode,po_type) select * from (
        select ROW_NUMBER () OVER (ORDER BY product_id) as id, product_id,pr_code,categ_type as product_category,parent_id as parent_category,invoice as lot_id, case when rejected=true then 'Reject' else 'Ok' end as rejected, avg(lot_price) as lot_price, avg(pur_price) as pur_price, avg(landed_cost) as landed_cost ,0 as opening_qty,0 as opening_value,
        
        min(COALESCE(date(receive_date),'2021-01-01')) as receive_date,
        
        0 as receive_qty,0 as receive_value,
        0 as issue_qty,
        0 as issue_value,
        sum(cloing_qty) as cloing_qty,
        case when avg(lot_price)>0 then sum(cloing_qty)*avg(lot_price) else sum(cloing_value) end as cloing_value,
        
        (select x_studio_shipment_mode from purchase_order where name=stock.po_number) as shipment_mode,
        
        (select po_type from purchase_order where name=stock.po_number) as po_type
        
        from(
        select
        product.id as product_id,product.default_code as pr_code,pt.categ_type,catype.parent_id,lot.id as invoice,lot.rejected,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as lot_price,
        
        (case when lot.id is not null then
        lot.pur_price else 0 end
        ) as pur_price,
        
        (case when lot.id is not null then
        lot.landed_cost else 0 end
        ) as landed_cost,
        
        0 as opening_qty,

        0 as opening_value,
        
        
        (select min(scheduled_date) from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product.id and sl.lot_id=lot.id and sl.state='done' and sl.reference like %s order by sl.picking_id asc)) as receive_date,
        (select origin from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product.id and sl.lot_id=lot.id and sl.state='done' and sl.reference like %s order by sl.picking_id asc) order by scheduled_date asc limit 1) as po_number,

        0 as receive_qty,

        0 as receive_value,

        0 as issue_qty,

        0 as issue_value,


        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) end
        ) as cloing_qty,

        (
        case when lot.id is not null then
		(select (sum(cl_qty)*avg(cost))+sum(lc_cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost, COALESCE((select sum(l.value) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id and l.description like %s),0) as lc_cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date <= %s and a.schedule_date <= %s) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date <= %s) end
        ) as cloing_value,
        
        pt.company_id

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        left join category_type as pcatype on catype.parent_id=pcatype.id
        left join stock_production_lot as lot on product.id=lot.product_id
        left join searching_date as sd on 1=1
        where pt.company_id = %s and (product.default_code like %s or product.default_code like %s)
        ) as stock where (stock.cloing_qty>=0 and stock.cloing_value>=0)
        group by stock.product_id,stock.pr_code,stock.categ_type,stock.parent_id,stock.invoice,stock.rejected,stock.company_id,stock.po_number
        ) as atb
        """
        self.env.cr.execute(query, ('%/IN/%','%/IN/%',to_date.date(),to_date.date(),'%LC/%',to_date.date(),to_date.date(),to_date.date(),self.env.company.id,'R_%','S_%'))




    def get_ageing(self,to_date):
        
        query_ = """truncate table stock_ageing;"""
        self.env.cr.execute(query_)
        
        
        query = """
        insert into stock_ageing(id,product_id,product_category,parent_category,lot_id,rejected,lot_price,pur_price,landed_cost,receive_date,duration,cloing_qty,cloing_value,slot_1,slot_2,slot_3,slot_4,slot_5,slot_6) 
        select * from (
        select ROW_NUMBER () OVER (ORDER BY product_id) as id,product_id,
        product_category,parent_category,lot_id, case when rejected=true then 'Reject' else 'Ok' end as rejected,lot_price,pur_price,
        landed_cost,receive_date,duration,cloing_qty,cloing_value,
        case when duration>=0 and duration<=30 then cloing_value else 0 end as slot_1,
        case when duration>30 and duration<=60 then cloing_value else 0 end as slot_2,
        case when duration>60 and duration<=90 then cloing_value else 0 end as slot_3,
        case when duration>90 and duration<=180 then cloing_value else 0 end as slot_4,
        case when duration>180 and duration<=365 then cloing_value else 0 end as slot_5,
        case when duration>365 then cloing_value else 0 end as slot_6
        from (
        select product_id,categ_type as product_category,parent_id as parent_category,invoice as lot_id, rejected, avg(lot_price) as lot_price, avg(pur_price) as pur_price, avg(landed_cost) as landed_cost,
        
        --sum(opening_qty) as opening_qty,
        --case when avg(lot_price)>0 then sum(opening_qty)*avg(lot_price) else sum(opening_value) end as opening_value,
        
        
        min(COALESCE(date(receive_date),'2021-01-01')) as receive_date, 
        DATE_PART('day',%s-min(COALESCE(receive_date,'2021-01-01 06:00:00'))) as duration,
        
        --sum(receive_qty) as receive_qty,
        --case when avg(lot_price)>0 then sum(receive_qty)*avg(lot_price) else sum(receive_value) end as receive_value,
        --sum(issue_qty) as issue_qty,
        --case when avg(lot_price)>0 then sum(issue_qty)*avg(lot_price) else sum(issue_value) end as issue_value,
        
        sum(cloing_qty) as cloing_qty,
        case when avg(lot_price)>0 then sum(cloing_qty)*avg(lot_price) else sum(cloing_value) end as cloing_value
        
        from(
        select
        product.id as product_id,pt.categ_type,catype.parent_id,lot.id as invoice,lot.rejected,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as lot_price,
        
        (case when lot.id is not null then
        lot.pur_price else 0 end
        ) as pur_price,
        
        (case when lot.id is not null then
        lot.landed_cost else 0 end
        ) as landed_cost,
        
        (select min(scheduled_date) from stock_picking where id in(select distinct sl.picking_id from stock_move_line as sl where sl.product_id=product.id and sl.lot_id=lot.id and sl.state='done' and sl.reference like %s order by sl.picking_id asc)) as receive_date,
        
        (
        case when lot.id is not null then
		(select COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) and b.lot_id=lot.id and b.product_id=product.id)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) end
        ) as cloing_qty,

        (
        case when lot.id is not null then
		(select (sum(cl_qty)*avg(cost))+sum(lc_cost) from ((select b.move_id,COALESCE(sum(case when b.location_dest_id in(8,9,36,10,37,38) then b.qty_done else -b.qty_done end),0) as cl_qty, COALESCE((select avg(l.unit_cost) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id),1) as cost, COALESCE((select sum(l.value) from stock_valuation_layer as l where l.product_id=product.id and l.stock_move_id=b.move_id and l.description like %s),0) as lc_cost
		from stock_move_line as b where move_id in(select stock_move_id from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) and b.lot_id=lot.id and b.product_id=product.id group by b.move_id)) as val)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=%s) end
        ) as cloing_value,
        
        pt.company_id

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        left join category_type as pcatype on catype.parent_id=pcatype.id
        left join stock_production_lot as lot on product.id=lot.product_id
        left join searching_date as sd on 1=1
        where pt.company_id = %s and (product.default_code like %s or product.default_code like %s)
        ) as stock where stock.cloing_qty>0
        group by stock.product_id,stock.categ_type,stock.parent_id,stock.invoice,stock.rejected,stock.company_id
        ) as atb) as ageing
        """
        self.env.cr.execute(query, (to_date,'%/IN/%',to_date,to_date,'%LC/%',to_date,to_date,self.env.company.id,'R_%','S_%'))        



    def get_price_comparison(self,from_date,to_date):
        com_month = from_date.date().strftime('%b, %Y')
        com_month = com_month + ' & ' + to_date.date().strftime('%b, %Y')
        # to_date

        query_ = """truncate table product_price_comparison;"""
        self.env.cr.execute(query_)
        query = """
        insert into product_price_comparison(id,product_id,product_template_id,pr_code,product_category,parent_category,comparison_month,second_last_price,last_price)
        select ROW_NUMBER () OVER (ORDER BY product_id) as id,product_id,product_template_id,pr_code,product_category,
        parent_category,comparison_month,second_last_price,last_price from (
        select product.id as product_id,
        pt.id as product_template_id,
        pt.uom_id as product_uom,
        product.default_code as pr_code,
        catype.id as product_category,
        catype.id as parent_category,
        %s as comparison_month,
        
        (select round((ol.price_unit / cast(po.currency_rate as decimal)),4) from purchase_order_line as ol 
        inner join purchase_order as po on po.id=ol.order_id
        where ol.product_id=product.id and date_part('month',po.date_approve)=%s
        and date_part('year',po.date_approve)=%s
        and po.state='purchase' and po.company_id=pt.company_id order by ol.id desc limit 1) as second_last_price,
        
        (select round((ol.price_unit / cast(po.currency_rate as decimal)),4) from purchase_order_line as ol
        inner join purchase_order as po on po.id=ol.order_id
        where ol.product_id=product.id and date_part('month',po.date_approve)=%s
        and date_part('year',po.date_approve)=%s
        and po.state='purchase' and po.company_id=pt.company_id order by ol.id desc limit 1) as last_price,
        
        pt.company_id

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        where pt.company_id = %s
        ) as stock
        """
        self.env.cr.execute(query, (com_month,from_date.month,from_date.year,to_date.month,to_date.year,self.env.company.id))        
