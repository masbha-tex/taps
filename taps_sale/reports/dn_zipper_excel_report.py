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
    _name = 'report.taps_sale.report_oa_zipper_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for packing'
    
    def generate_xlsx_report(self, workbook, data, orders):
        report_name = orders.name
        
        docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
        
        report_data = []
        order_data = []
        slnumber=0
        customer = ''
        pi_num = ''
        oa_num = ''
        create_date = ''
        expected_date = ''
        for x,o_data in enumerate(docs):
            slnumber = slnumber+1
            if x == 0:
                customer = "\n".join([orders.partner_id.name,"\n",orders.buyer_name.name,orders.payment_term_id.name])
                pi_num = orders.order_ref.pi_number
                oa_num = orders.name
                create_date = orders.create_date.strftime("%d-%m-%Y")
                expected_date = orders.expected_date.strftime("%d-%m-%Y")
            else:
                customer = ''
                pi_num = ''
                oa_num = ''
                create_date = ''
                expected_date = ''
            
            pr_name = o_data.product_template_id.name
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
            finish = o_data.finish #.replace('\n',' ')
            shade = o_data.shade
            shadewise_tape = o_data.shadewise_tape
            
            # filtered_name = [x for x in report_data if x[1] == o_data.product_template_id.name]
            # if filtered_name:
            #     pr_name = ''
            
#             filtered_slider = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and x[2] == o_data.slidercodesfg]
#             if filtered_slider:
#                 slider = ''

#             filtered_finish = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and x[3] == o_data.finish]
#             if filtered_finish:
#                 finish = ''
                
            # filtered_pi_num = [x for x in report_data if x[4] == orders.order_ref.pi_number]
            # if filtered_pi_num:
            #     pi_num = ''
            
            # filtered_create_date = [x for x in report_data if x[6] == orders.create_date.strftime("%d-%m-%Y")]
            # if filtered_create_date:
            #     create_date = ''
            
            # filtered_expected_date = [x for x in report_data if x[5] == orders.expected_date.strftime("%d-%m-%Y")]
            # if filtered_expected_date:
            #     expected_date = ''
            
#             filtered_shade = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and x[9] == o_data.shade]
#             if filtered_shade:
#                 shade = ''
                
#             filtered_shadewise_tape = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and  x[9] == o_data.shade and x[16] == o_data.shadewise_tape]
#             if filtered_shadewise_tape:
#                 shadewise_tape = ''
                
            
            sizein = o_data.sizein
            sizecm = o_data.sizecm
            if sizein == 'N/A':
                sizein = ''
            if sizecm == 'N/A':
                sizecm = ''
            

            order_data = [
                customer,
                pr_name,
                slider,
                finish,
                pi_num,
                oa_num,
                create_date,
                '',
                '',
                #expected_date,
                shade,
                sizein,
                sizecm,
                o_data.product_uom_qty,
                '',
                o_data.product_uom_qty,
                o_data.tape_con,
                shadewise_tape,
                o_data.wire_con,
                o_data.slider_con,
                o_data.botomwire_con,
                o_data.topwire_con,
                #o_data.pinbox_con,
                orders.sale_representative.name,
            ]
            report_data.append(order_data)
        
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # worksheet = workbook.add_worksheet()
        
        
        qty_total = 0
        shade_total = 0
        wire_total = 0
        slider_total = 0
        bottom_total = 0
        top_total = 0
        
        sheet = workbook.add_worksheet(report_name[:41])
        #bold = workbook.add_format({'bold': True})
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})
        _range = len(report_data)
        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(9, 9, 40)
        sheet.merge_range(1, 0, _range, 0, '', merge_format)
        #sheet.merge_range(1, 1, _range, 1, '', merge_format)
        #sheet.merge_range(1, 2, _range, 2, '', merge_format)
        #sheet.merge_range(1, 3, _range, 3, '', merge_format)
        sheet.merge_range(1, 4, _range, 4, '', merge_format)
        sheet.merge_range(1, 5, _range, 5, '', merge_format)
        sheet.merge_range(1, 6, _range, 6, '', merge_format)
        sheet.merge_range(1, 7, _range, 7, '', merge_format)
        sheet.merge_range(1, 8, _range, 8, '', merge_format)
        
        sheet.write(0, 0, "CUSTOMER NAME", column_style)
        sheet.write(0, 1, "PRODUCT", column_style)
        sheet.write(0, 2, "SLIDER CODE", column_style)
        sheet.write(0, 3, "FINISH", column_style)
        sheet.write(0, 4, "PI NO", column_style)
        sheet.write(0, 5, "OA NO", column_style)
        sheet.write(0, 6, "OA DATE", column_style)
        sheet.write(0, 7, "Production DATE", column_style)
        sheet.write(0, 8, "DETAILS", column_style)
        #sheet.write(1, 9, "DELIVERY DATE", column_style)
        sheet.write(0, 9, "SHADE", column_style)
        sheet.write(0, 10, "SIZE(INCH)", column_style)
        sheet.write(0, 11, "SIZE(CM)", column_style)
        sheet.write(0, 12, "ORDER QTY", column_style)
        sheet.write(0, 13, "READY QTY", column_style)
        sheet.write(0, 14, "PENDING QTY", column_style)
        sheet.write(0, 15, "TOTAL WT/KG", column_style)
        sheet.write(0, 16, "SHADE TOTAL", column_style)
        sheet.write(0, 17, "WIRE/KG", column_style)
        sheet.write(0, 18, "SLIDER/PCS", column_style)
        sheet.write(0, 19, "H-BOTTOM/KG", column_style)
        sheet.write(0, 20, "U-TOP/KG", column_style)
        #sheet.write(0, 18, "PINBOX/KG", column_style)
        sheet.write(0, 21, "SALESPERSON", column_style)
        col = 0
        row = 1
        row_ = 0
        
        product_range = 0
        slider_range = 0
        finish_range = 0
        shade_range = 0
        
        for line in report_data:
            for x in report_data[row_:]:
                p_last_one = row
                sl_last_one = row
                f_last_one = row
                last_one = row
                if (x[1] == line[1]):
                    product_range += 1
                else:
                    sheet.merge_range(row, 1, product_range, 1, '', merge_format)
                    product_range = row
                    
                if (x[2] == line[2]):
                    slider_range += 1
                else:
                    sheet.merge_range(row, 2, slider_range, 2, '', merge_format)
                    slider_range = row
                    
                if (x[3] == line[3]): 
                    finish_range += 1
                else:
                    sheet.merge_range(row, 3, finish_range, 3, '', merge_format)
                    finish_range = row
                
                if (x[9] == line[9]):
                    shade_range += 1
                else:
                    sheet.merge_range(row, 9, shade_range, 9, '', merge_format)
                    sheet.merge_range(row, 16, shade_range, 16, '', merge_format_)
                    shade_range = row
                
                if _range == product_range:
                    sheet.merge_range(p_last_one, 1, product_range, 1, '', merge_format)
                    product_range = row
                if _range == slider_range:
                    sheet.merge_range(sl_last_one, 2, slider_range, 2, '', merge_format)
                    slider_range = row
                if _range == finish_range:
                    sheet.merge_range(f_last_one, 3, finish_range, 3, '', merge_format)
                    finish_range = row
                if _range == shade_range:
                    sheet.merge_range(last_one, 9, shade_range, 9, '', merge_format)
                    sheet.merge_range(last_one, 16, shade_range, 16, '', merge_format_)
                    shade_range = row
            
            col=0
            for l in line:
                if col in(0,6,7):
                    sheet.write(row, col, l, format_label_1)
                elif col in(1,2,3):
                    sheet.write(row, col, l, format_label_2)
                elif col in(4,5):
                    sheet.write(row, col, l, format_label_3)
                elif col in(8,9):
                    sheet.write(row, col, l, format_label_4)
                elif col == 14:
                    sheet.write(row, col, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                else:
                    sheet.write(row, col, l, row_style)
                if col == 12:
                    qty_total += l
                if col == 15:
                    shade_total += l
                if col == 17:
                    wire_total += l
                if col == 18:
                    slider_total += l
                if col == 19:
                    bottom_total += l
                if col == 20:
                    top_total += l
                col+=1
                
            row+=1
            row_+=1
        
        sheet.write(row, 0, '')
        sheet.write(row, 1, '')
        sheet.write(row, 2, '')
        sheet.write(row, 3, '')
        sheet.write(row, 4, '')
        sheet.write(row, 5, '')
        sheet.write(row, 6, '')
        sheet.write(row, 7, '')
        sheet.write(row, 8, '')
        sheet.write(row, 9, '')
        sheet.write(row, 10, '')
        sheet.write(row, 11, '')
        sheet.write(row, 12, '=SUM(M{0}:M{1})'.format(2, row), row_style)
        sheet.write(row, 13, '=SUM(N{0}:N{1})'.format(2, row), row_style)
        sheet.write(row, 14, '=M{1}-N{1}'.format(row+1, row+1), row_style)
        sheet.write(row, 15, '')
        sheet.write(row, 16, shade_total, row_style)
        sheet.write(row, 17, wire_total, row_style)
        sheet.write(row, 18, slider_total, row_style)
        sheet.write(row, 19, bottom_total, row_style)
        sheet.write(row, 20, top_total, row_style)
        sheet.write(row, 21, '')
        
        #'=SUM({0}:{1})'.format(cell_sum_start, cell_sum_end)
        
        #sheet['M37'] = '= SUM(M2:M30)'