import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
import re
import math



class SalesXlsx(models.AbstractModel):
    _name = 'report.taps_sale.report_sa_zipper_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for Sample'
    
    def generate_xlsx_report(self, workbook, data, sale_orders):
        report_name = 'Running Orders'#orders.name
        # raise UserError((m_orders.oa_id.ids))
        # sale_orders = self.env['sale.order'].browse(m_orders.oa_id.ids)

        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})
        
        sheet.write(0, 0, "BUYER & CUSTOMER NAME", column_style)
        sheet.write(0, 1, "PRODUCT", column_style)
        sheet.write(0, 2, "SLIDER CODE", column_style)
        # sheet.write(0, 3, "FINISH", column_style)
        # sheet.write(0, 4, "PI NO", column_style)
        sheet.write(0, 3, "SA NO", column_style)
        sheet.write(0, 4, "SA DATE", column_style)
        sheet.write(0, 5, "DELIVERY DATE", column_style)
        sheet.write(0, 6, "DELIVERY ON", column_style)
        #sheet.write(1, 9, "DELIVERY DATE", column_style)
        sheet.write(0, 7, "SHADE", column_style)
        sheet.write(0, 8, "SIZE(INCH)", column_style)
        sheet.write(0, 9, "SIZE(CM)", column_style)
        sheet.write(0, 10, "ORDER QTY", column_style)
        sheet.write(0, 11, "READY QTY", column_style)
        sheet.write(0, 12, "PENDING QTY", column_style)
        sheet.write(0, 13, "STYLE REF.", column_style)
        # sheet.write(0, 16, "SHADE TOTAL", column_style)
        # sheet.write(0, 17, "WIRE/KG", column_style)
        # sheet.write(0, 18, "SLIDER/PCS", column_style)
        # sheet.write(0, 19, "H-BOTTOM/KG", column_style)
        # sheet.write(0, 20, "U-TOP/KG", column_style)
        #sheet.write(0, 18, "PINBOX/KG", column_style)
        sheet.write(0, 14, "KIND ATTENTION", column_style)
        sheet.write(0, 15, "DETAILS", column_style)
        row_rang = 1
        _range = 0
        
        row_p = 0
        row_sl = 0
        row_sh = 0
        
        product_range = 0
        slider_range = 0
        shade_range = 0
        sale_orders = sorted(sale_orders, key=lambda r: r.id, reverse=False)
        for orders in sale_orders:
            docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
            
            
            report_data = []
            order_data = []
            slnumber=0
            customer = ''
            oa_num = ''
            remarks = ''
            create_date = ''
            delivery_date = ''
            for x,o_data in enumerate(docs):
                slnumber = slnumber+1
                if x == 0:
                    customer = "\n".join([orders.partner_id.name,"\n",orders.buyer_name.name])
                    oa_num = orders.name
                    remarks = orders.remarks
                    create_date = orders.create_date.strftime("%d-%m-%Y")
                    if orders.commitment_date:
                        delivery_date = orders.commitment_date.strftime("%d-%m-%Y")
                else:
                    customer = ''
                    oa_num = ''
                    remarks = ''
                    create_date = ''
                    delivery_date = ''
                
                pr_name = o_data.product_template_id.name
                if o_data.finish:
                    pr_name = "\n".join([pr_name,o_data.finish])
                if o_data.numberoftop:
                    pr_name = "\n".join([pr_name,o_data.numberoftop])
                if o_data.ptopfinish:
                    pr_name = "\n".join([pr_name,o_data.ptopfinish])
                if o_data.pbotomfinish:
                    pr_name = "\n".join([pr_name,o_data.pbotomfinish])
                if o_data.ppinboxfinish:
                    pr_name = "\n".join([pr_name,o_data.ppinboxfinish])
                if o_data.topbottom:
                    pr_name = "\n".join([pr_name,o_data.topbottom])
                slider = o_data.slidercodesfg
                # finish = o_data.finish #.replace('\n',' ')
                shade = o_data.shade
                
                sizein = o_data.sizein
                sizecm = o_data.sizecm
                if sizein == 'N/A':
                    sizein = ''
                if sizecm == 'N/A':
                    sizecm = ''
                
                # m_order = self.env['manufacturing.order'].search([('sale_order_line','=',o_data.id)])
                # ready_qty = sum(m_order.mapped('done_qty'))
                # raise UserError((o_data.id,ready_qty))
                # balance_qty = o_data.product_uom_qty-ready_qty
                order_data = [
                    customer,
                    pr_name,
                    slider,
                    oa_num,
                    create_date,
                    delivery_date,
                    '',
                    shade,
                    sizein,
                    sizecm,
                    o_data.product_uom_qty,
                    '',
                    o_data.product_uom_qty,
                    orders.style_ref,
                    orders.kind_attention,
                    remarks,
                ]
                report_data.append(order_data)
                
            if _range > 0:
                _range += 1
            _range += len(report_data)
            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(14, 14, 20)
            sheet.set_column(15, 15, 40)
            sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
            #sheet.merge_range(1, 1, _range, 1, '', merge_format)
            #sheet.merge_range(1, 2, _range, 2, '', merge_format)
            #sheet.merge_range(1, 3, _range, 3, '', merge_format)
            sheet.merge_range(row_rang, 3, _range, 3, '', merge_format)
            sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
            sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
            sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
            sheet.merge_range(row_rang, 14, _range, 14, '', merge_format)
            sheet.merge_range(row_rang, 15, _range, 15, '', merge_format)
            
            # qty_total = 0
            
            
            col = 0
            row = row_rang
            inline_row = 1
            row_p = 0
            row_sl = 0
            row_f = 0
            row_sh = 0
            
            product_range += product_range
            slider_range += slider_range
            shade_range += shade_range
            
            for line in report_data:
                    
                for x in report_data[row_p:]:
                    p_last_one = row
                    if (x[1] == line[1]):
                        product_range += 1
                        row_p += 1
                    else:
                        sheet.merge_range(row, 1, product_range, 1, '', merge_format)
                        product_range = row
                        break
                    if _range == product_range:
                        sheet.merge_range(p_last_one, 1, product_range, 1, '', merge_format)
                        product_range = row
                for x in report_data[row_sl:]:
                    sl_last_one = row
                    if (x[2] == line[2]):
                        slider_range += 1
                        row_sl += 1
                    else:
                        sheet.merge_range(row, 2, slider_range, 2, '', merge_format)
                        slider_range = row
                        break
                    if _range == slider_range:
                        sheet.merge_range(sl_last_one, 2, slider_range, 2, '', merge_format)
                        slider_range = row
    
                for x in report_data[row_sh:]:
                    last_one = row
                    if (x[9] == line[9]):
                        shade_range += 1
                        row_sh += 1
                    else:
                        sheet.merge_range(row, 9, shade_range, 9, '', merge_format)
                        sheet.merge_range(row, 16, shade_range, 16, '', merge_format_)
                        shade_range = row
                        break
                    if _range == shade_range:
                        sheet.merge_range(last_one, 9, shade_range, 9, '', merge_format)
                        sheet.merge_range(last_one, 16, shade_range, 16, '', merge_format_)
                        shade_range = row
                        
                col = 0
                for l in line:
                    if col in(0,3,4,5,6):
                        sheet.write(row, col, l, format_label_1)
                    elif col in(1,2,7):
                        sheet.write(row, col, l, format_label_2)
                    # elif col in(4,5):
                    #     sheet.write(row, col, l, format_label_3)
                    elif col in(14,15):
                        sheet.write(row, col, l, format_label_4)
                    elif col == 12:
                        sheet.write(row, col, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                    else:
                        sheet.write(row, col, l, row_style)
                    # if col == 12:
                    #     qty_total += l
                    col += 1
                    
                row += 1
                inline_row += 1
                row_p = row_sl = row_f = row_sh = inline_row-1
            
            # sheet.write(row, 0, '')
            # sheet.write(row, 1, '')
            # sheet.write(row, 2, '')
            # sheet.write(row, 3, '')
            # sheet.write(row, 4, '')
            # sheet.write(row, 5, '')
            # sheet.write(row, 6, '')
            # sheet.write(row, 7, '')
            # sheet.write(row, 8, '')
            # sheet.write(row, 9, '')
            # sheet.write(row, 10, '=SUM(M{0}:M{1})'.format(row_rang+1, row), row_style)
            # sheet.write(row, 11, '=SUM(N{0}:N{1})'.format(row_rang+1, row), row_style)
            # sheet.write(row, 12, '=M{1}-N{1}'.format(row+1, row+1), row_style)
            # sheet.write(row, 13, '')
            # sheet.write(row, 14, '')

            row_rang = row + 1