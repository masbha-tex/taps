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

    report_by = fields.Selection([
        ('by_categories', 'By Categories'),
        ('by_items', 'By Items')], 
        default='by_categories')
    categ_ids = fields.Many2many('category.type', string='Categories')
    product_ids = fields.Many2many('product.product')
    from_date = fields.Date('From')
    to_date = fields.Date('To', default=fields.Date.context_today)
    file_data = fields.Binary(readonly=True, attachment=False)
    is_spare = fields.Boolean(string='Is a RM', default=False,
        help="Check if the product is a RM, otherwise it is a Spare Parts")
    stock_type = fields.Selection(string='Stock of',
                                    selection=[('rm', 'RM'), ('spare', 'Spare Parts')],
                                  compute='_compute_stock_type', inverse='_write_stock_type')
    
    @api.depends('is_spare')
    def _compute_stock_type(self):
        for stock in self:
            stock.stock_type = 'spare' if stock.is_spare else 'rm'

    def _write_stock_type(self):
        for stock in self:
            stock.is_spare = stock.stock_type == 'spare'

    @api.onchange('stock_type')
    def onchange_company_type(self):
        self.is_spare = (self.stock_type == 'spare')
        
    def getopening_qty(self,productid,lotid,fr_date):#lotid,
        #stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<', fr_date)])
        query = """ select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as op_qty from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<%s """
        
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, (lotid, productid, fr_date))
        result = cursor.fetchall()
        qty = result[0][0]
        return qty
    
    def getopening_val(self,productid,lotid,from_date):
        prev_date = datetime.strptime('2022-04-01', '%Y-%m-%d')
        if from_date>prev_date:
            query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<%s """
            cr = self._cr
            cursor = self.env.cr
            cr.execute(query, (lotid, productid, prev_date))
            val_1 = cursor.fetchall()
            
            query_ = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description not like %s and b.lot_id=%s and  a.product_id=%s and a.schedule_date<%s and a.schedule_date>=%s """
            cr_ = self._cr
            cursor_ = self.env.cr
            cr_.execute(query_, ('%LC/%',lotid, productid, from_date, prev_date))
            val_2 = cursor_.fetchall()
            
            #val = val_1 + val_2
            
            landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', prev_date),('date', '<', from_date.date())])

            pickinglist = landedcost.mapped('picking_ids.id')#picking_ids
            lclist = landedcost.mapped('id')
            
            picking_details = self.env['stock.move.line'].search([('state', '=', 'done'),('product_id', '=', productid)
                                                                  ,('lot_id', '=', lotid),('picking_id', 'in', pickinglist)])
            lot_qty = sum(picking_details.mapped('qty_done'))
            
            #raise UserError((lclist))
            #lc_details = self.env['stock.valuation.adjustment.lines'].search([('product_id', '=', productid),('cost_id', 'in', (lclist))])
            _query = """ select COALESCE(sum(additional_landed_cost/quantity),0) as price from stock_valuation_adjustment_lines where product_id=%s and cost_id in (%s) """
            _cr_ = self._cr
            _cursor = self.env.cr
            _cr_.execute(_query, (productid, lclist[0]))
            val_3 = _cursor.fetchall()
            val_3 = val_3*lot_qty
            val = val_1[0][0] + val_2[0][0] + val_3[0][0]
        else:
            query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<%s """
            cr = self._cr
            cursor = self.env.cr
            cr.execute(query, (lotid, productid, from_date))
            result = cursor.fetchall()
            val = result[0][0]
            #return val
        return val
    
    def getreceive_qty(self,productid,lotid,from_date,to_date):
        query = """ select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as re_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like %s or a.description like %s) and b.lot_id=%s and  a.product_id=%s and a.schedule_date>=%s and a.schedule_date<=%s """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, ('%/IN/%','%/OUT/%',lotid, productid, from_date, to_date))
        result = cursor.fetchall()
        qty = result[0][0]
        return qty
    
    def getreceive_val(self,productid,lotid,from_date,to_date):
        query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as re_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like %s or a.description like %s) and b.lot_id=%s and  a.product_id=%s and a.schedule_date>=%s and a.schedule_date<=%s """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, ('%/IN/%','%/OUT/%',lotid, productid, from_date, to_date))
        result = cursor.fetchall()
        val = result[0][0]


        
        landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', from_date.date()),('date', '<=', to_date.date())])
        
        pickinglist = landedcost.mapped('picking_ids.id')
        lclist = landedcost.mapped('id')
        
        picking_details = self.env['stock.move.line'].search([('state', '=', 'done'),('product_id', '=', productid)
                                                              ,('lot_id', '=', lotid),('picking_id', 'in', pickinglist)])
        lot_qty = sum(picking_details.mapped('qty_done'))
        
        _query = """ select COALESCE(sum(additional_landed_cost/quantity),0) as price from stock_valuation_adjustment_lines where product_id=%s and cost_id in (%s) """
        _cr_ = self._cr
        _cursor = self.env.cr
        _cr_.execute(_query, (productid, lclist[0]))
        result = _cursor.fetchall()
        val_1 = result[0][0]
        val_1 = val_1*lot_qty
        val = val + val_1
        return val
    
    def getissue_qty(self,productid,lotid,from_date,to_date):
        query = """ select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as isue_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like %s and b.lot_id=%s and  a.product_id=%s and a.schedule_date>=%s and a.schedule_date<=%s """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, ('%/MR/%',lotid, productid, from_date, to_date))
        result = cursor.fetchall()
        qty = result[0][0]
        return qty
    
        #stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '>=', from_date),('schedule_date', '<=', to_date),('description','like','%/MR/%')])#,('description','not like','%Product Quantity Updated%') #('quantity', '<', 0),
        #qty = sum(stock_details.mapped('quantity'))
    
    def getissue_val(self,productid,lotid,from_date,to_date):
        query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as isue_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like %s and b.lot_id=%s and  a.product_id=%s and a.schedule_date>=%s and a.schedule_date<=%s """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, ('%/MR/%',lotid, productid, from_date, to_date))
        result = cursor.fetchall()
        val = result[0][0]
        return val
    
        #stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '>=', from_date),('schedule_date', '<=', to_date),('description','like','%/MR/%')])#,('description','not like','%Product Quantity Updated%') #('quantity', '<', 0),
        #val = sum(stock_details.mapped('value'))

    def getclosing_qty(self,productid,lotid,to_date):
        query = """ select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as closing_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<=%s """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, (lotid, productid, to_date))
        result = cursor.fetchall()
        qty = result[0][0]
        return qty
        #stock_details = self.env['stock.valuation.layer'].search([('product_id', '=', productid),('schedule_date', '<=', to_date)])
        #qty = sum(stock_details.mapped('quantity'))
    
    def getclosing_val(self,productid,lotid,to_date):
        prev_date = datetime.strptime('2022-04-01', '%Y-%m-%d')
        if to_date>prev_date:
            
            query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<%s """
            cr = self._cr
            cursor = self.env.cr
            cr.execute(query, (lotid, productid, prev_date))
            result_1 = cursor.fetchall()
            val_1 = result_1[0][0]
            
            query_ = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description not like %s and b.lot_id=%s and  a.product_id=%s and a.schedule_date<=%s and a.schedule_date>=%s """
            cr_ = self._cr
            cursor_ = self.env.cr
            cr_.execute(query_, ('%LC/%',lotid, productid, to_date, prev_date))
            result_2 = cursor_.fetchall()
            val_2 = result_2[0][0]
            
            landedcost = self.env['stock.landed.cost'].search([('state', '=', 'done'),('date', '>=', prev_date),('date', '<=', to_date.date())])

            pickinglist = landedcost.mapped('picking_ids.id')#picking_ids
            lclist = landedcost.mapped('id')
            
            picking_details = self.env['stock.move.line'].search([('state', '=', 'done'),('product_id', '=', productid)
                                                                  ,('lot_id', '=', lotid),('picking_id', 'in', pickinglist)])
            lot_qty = sum(picking_details.mapped('qty_done'))
            
            _query = """ select COALESCE(sum(additional_landed_cost/quantity),0) as price from stock_valuation_adjustment_lines where product_id=%s and cost_id in (%s) """
            _cr_ = self._cr
            _cursor = self.env.cr
            _cr_.execute(_query, (productid, lclist[0]))
            result_3 = _cursor.fetchall()
            val_3 = result_3[0][0]
            
            val_3 = val_3*lot_qty
            val = val_1 + val_2 + val_3
        else:
            query = """ select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as cl_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=%s and  a.product_id=%s and a.schedule_date<=%s """
            cr = self._cr
            cursor = self.env.cr
            cr.execute(query, (lotid, productid, to_date))
            result = cursor.fetchall()
            val = result[0][0]
        return val
        
    def float_to_time(self,hours):
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(round(60 * fractional, precision_digits=0)), 0)    
    
    def print_date_wise_stock_register(self):
        Move = self.env['stock.valuation.layer']
        product = self.env['product.product'].search([('default_code', 'like', 'R_')])
        start_time = fields.datetime.now()
        f_date = self.from_date
        t_date = self.to_date
        hour_from = 0.0
        hour_to = 23.98
        combine = datetime.combine
        from_date = combine(f_date, self.float_to_time(hour_from))
        to_date = combine(t_date, self.float_to_time(hour_to))
        #raise UserError((from_date,to_date))
        if not (self.product_ids or self.categ_ids or self.is_spare == 1):
            products = product.search([('type', '=', 'product'),('default_code', 'like', 'R_')])
        elif not (self.product_ids or self.categ_ids or self.is_spare == 0):
            products = product.search([('type', '=', 'product'),('default_code', 'like', 'S_')])
        elif self.report_by == 'by_items':
            products = self.product_ids
        elif (self.is_spare == 0):
            products = product.search([('categ_type', 'in', self.categ_ids.ids),('default_code', 'like', 'R_')])
        else:
            products = product.search([('categ_type', 'in', self.categ_ids.ids),('default_code', 'like', 'S_')])
        # Date wise opening quantity
        #product_quantities = products._compute_quantities_dict(False, False, False, from_date, to_date)
        #products = products.sorted(key = 'categ_type')
        
        #product_id = products.mapped('id')
        
        #lot_details = self.env['stock.move.line'].search([('product_id', 'in', (product_id))])
        
        
        
        report_data = []
        
        
        calist = products.mapped('categ_type')
        calist = calist.mapped('id')
        Catype = self.env['category.type']
        Catypes = Catype.search([('id', 'in', (calist))])
        sort_ca_type = Catypes.sorted(key = 'parent_id')
        
        for categ in sort_ca_type:
            if (self.is_spare != 1):
                if(categ.name == 'Spare Parts' or categ.parent_id.name == 'Spare Parts'):
                    continue
            #report_data.append([categ.display_name])
            categ_products = products.filtered(lambda x: x.categ_type == categ)
            #stock_details = self.env['category.type'].search([('product_id', '=', productid),('schedule_date', '<', to_date)])
            report_product_data = []
            product_cat_data = []
            for product in categ_products:
                product_data = []
                received_qty = received_price_unit = issued_qty = issued_value = 0
                product_id = product.id
                
                lot_details = self.env['stock.production.lot'].search([('product_id', '=', (product_id))])
                if lot_details:
                    report_lot_data = []
                    for l in lot_details:
                        lot_data = []
                        opening_qty = opening_value = received_qty = received_value = issued_qty = issued_value = closing_qty = closing_value = 0
                        
                        opening_qty = self.getopening_qty(product_id,l.id,from_date)
                        if opening_qty>0:
                            opening_value = self.getopening_val(product_id,l.id,from_date)
                        received_qty = self.getreceive_qty(product_id,l.id,from_date,to_date)
                        if received_qty>0:
                            received_value =  self.getreceive_val(product_id,l.id,from_date,to_date)
                        received_qty = round(received_qty,2)
                        received_value = round(received_value,2)
                        
                        issued_qty = self.getissue_qty(product_id,l.id,from_date,to_date)
                        issued_qty = round(abs(issued_qty),2)
                        if issued_qty:
                            issued_value = self.getissue_val(product_id,l.id,from_date,to_date)
                        issued_value = round(abs(issued_value),2)
                        closing_qty = self.getclosing_qty(product_id,l.id,to_date)
                        closing_qty = round(closing_qty,2)
                        if closing_qty>0:
                            closing_value = self.getclosing_val(product_id,l.id,to_date)
                        closing_value = round(closing_value,2) 
                            
                            
                            
                        if abs(abs(opening_qty)+abs(received_qty)+abs(issued_qty))>0:
                            lot_data = [
                                '',
                                '',
                                '',
                                l.name,
                                opening_qty,
                                opening_value,
                                received_qty,
                                received_value,
                                issued_qty,
                                issued_value,
                                closing_qty,
                                closing_value,
                                l.x_studio_rejected,
                            ]
                            report_lot_data.append(lot_data)

#                 # Prepare Opening Data
#                 #raise UserError((product_id,from_date))
#                 opening_qty = self.getopening_qty(product_id,l.id,from_date)#product_quantities[product_id]['qty_available']
#                 opening_qty = round(opening_qty,2)
#                 if opening_qty<=0:
#                     opening_value = 0
#                 else:
#                     opening_value = self.getopening_val(product_id,l.id,from_date)#round(opening_qty * product.standard_price, precision_rounding=4)
                
#                 opening_value = round(opening_value,2)
#                 # Prepare Received data
#                 #if in_move_dict.get(product_id):
#                 received_qty = self.getreceive_qty(product_id,l.id,from_date,to_date)#in_move_dict[product_id][0]
#                     #received_price_unit = in_move_dict[product_id][1]
#                 received_value =  self.getreceive_val(product_id,l.id,from_date,to_date)#round(received_qty * received_price_unit, precision_rounding=4)
#                 received_qty = round(received_qty,2)
#                 received_value = round(received_value,2)                
#                 # prepare Issued Data
#                 #if out_move_dict.get(product_id):
#                 issued_qty = self.getissue_qty(product_id,l.id,from_date,to_date)# out_move_dict[product_id][0]
#                 issued_qty = round(abs(issued_qty),2)
#                 if issued_qty<=0:
#                     issued_value = 0
#                 else:
#                     issued_value = self.getissue_val(product_id,l.id,from_date,to_date) #(issued_qty * out_move_dict[product_id][1])
                
#                 issued_value = round(abs(issued_value),2)
#                 # Prepare Closing Quantity
#                 closing_qty = self.getclosing_qty(product_id,l.id,to_date)# opening_qty + received_qty - issued_qty #
#                 closing_qty = round(closing_qty,2)
#                 if closing_qty<=0:
#                     closing_value = 0
#                 else:
#                     closing_value = self.getclosing_val(product_id,l.id,to_date)# opening_value + received_value - issued_value #
#                 closing_value = round(closing_value,2) 

                opening_pro_qty=sum(row[4] for row in report_lot_data)
                opening_pro_value=sum(row[5] for row in report_lot_data)
                received_pro_qty=sum(row[6] for row in report_lot_data)
                received_pro_value=sum(row[7] for row in report_lot_data)
                issued_pro_qty=sum(row[8] for row in report_lot_data)
                issued_pro_value=sum(row[9] for row in report_lot_data)
                closing_pro_qty=sum(row[10] for row in report_lot_data)
                closing_pro_value=sum(row[11] for row in report_lot_data)
                
                if abs(abs(opening_qty)+abs(received_qty)+abs(issued_qty))>0:
                    product_data = [
                        '',
                        '',
                        product.name,
                        '',
                        opening_pro_qty,
                        opening_pro_value,
                        received_pro_qty,
                        received_pro_value,
                        issued_pro_qty,
                        issued_pro_value,
                        closing_pro_qty,
                        closing_pro_value,
                        '',
                    ]
                    report_product_data.append(product_data)
            
            opening_categ_qty=sum(row[4] for row in report_product_data)
            opening_categ_value=sum(row[5] for row in report_product_data)
            received_categ_qty=sum(row[6] for row in report_product_data)
            received_categ_value=sum(row[7] for row in report_product_data)
            issued_categ_qty=sum(row[8] for row in report_product_data)
            issued_categ_value=sum(row[9] for row in report_product_data)
            closing_categ_qty=sum(row[10] for row in report_product_data)
            closing_categ_value=sum(row[11] for row in report_product_data)
            
            parent_type = ''
            if categ.parent_id.name:
                parent_type = categ.parent_id.name
            product_cat_data = [
                parent_type,
                categ.name,
                '',
                opening_categ_qty,
                opening_categ_value,
                received_categ_qty,
                received_categ_value,
                issued_categ_qty,
                issued_categ_value,
                closing_categ_qty,
                closing_categ_value,
                '',
            ]
            
            report_data.append(product_cat_data)
            if self.report_by == 'by_items':
                for prodata in report_product_data:
                    report_data.append(prodata)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#C8EAAB'})
        worksheet.merge_range('C2:F2', 'RM Stock Report', report_title_style)

        report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14})
        worksheet.write(3, 3, ('From %s to %s' % (format_date(self.env, from_date), format_date(self.env, to_date))), report_small_title_style)

        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#EEED8A', 'font_size': 12})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})
        reject_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F'})

        # set the width od the column
        
        worksheet.set_column(0, 11, 20)
        
        worksheet.write(6, 0, 'Product', column_product_style)        
        worksheet.write(6, 1, 'Category', column_product_style)
        worksheet.write(6, 2, 'Item', column_product_style)
        worksheet.write(6, 3, 'Invoice', column_product_style)
        worksheet.write(6, 4, 'Opening Quantity', column_product_style)
        worksheet.write(6, 5, 'Opening Value', column_product_style)
        worksheet.write(6, 6, 'Received Quantity', column_received_style)
        worksheet.write(6, 7, 'Received Value', column_received_style)
        worksheet.write(6, 8, 'Issued Quantity', column_issued_style)
        worksheet.write(6, 9, 'Issued Value', column_issued_style)
        worksheet.write(6, 10, 'Closing Quantity', column_product_style)
        worksheet.write(6, 11, 'Closing Value', column_product_style)
        col = 0
        row=7
        
        for line in report_data:
            col=0
            categ=False
            for l in line:
                if l != '' and col==1 :
                    categ=True
                if categ==True:
                    worksheet.write(row, col, l, row_categ_style)
                else:
                    if line[11] == True:
                        worksheet.write(row, col, l, reject_style)
                    else:
                        worksheet.write(row, col, l)
                col+=1
            row+=1
        workbook.close()
        xlsx_data = output.getvalue()

        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, 'StockRegisterReport'),
            'target': 'self',
        }