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
        
        # raise UserError((docs.id))
        
        report_data = []
        order_data = []
        slnumber=0
        customer = ''
        pi_num = ''
        oa_num = ''
        for o_data in docs:
            slnumber = slnumber+1
            # if customer:
            #     customer = ''
            #     pi_num = ''
            #     oa_num = ''
            # else:
            customer = "\n".join([orders.partner_id.name,orders.buyer_name.name,orders.payment_term_id.name])
            pi_num = orders.order_ref.pi_number
            oa_num = orders.name
            
            pr_name = o_data.product_template_id.name
            slider = o_data.slidercodesfg
            finish = o_data.finish
            create_date = orders.create_date.strftime("%d-%m-%Y")
            expected_date = orders.expected_date.strftime("%d-%m-%Y")
            shade = o_data.shade
            shadewise_tape = o_data.shadewise_tape
            
            filtered_name = [x for x in report_data if x[1] == o_data.product_template_id.name]
            if filtered_name:
                pr_name = ''
            
            filtered_slider = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and x[2] == o_data.slidercodesfg]
            if filtered_slider:
                slider = ''

            filtered_finish = [x for x in report_data if (x[1] == o_data.product_template_id.name or x[1] == '') and x[3] == o_data.finish]
            if filtered_finish:
                finish = ''
                
            # filtered_pi_num = [x for x in report_data if x[4] == orders.order_ref.pi_number]
            # if filtered_pi_num:
            #     pi_num = ''
            
            filtered_create_date = [x for x in report_data if x[6] == orders.create_date.strftime("%d-%m-%Y")]
            if filtered_create_date:
                create_date = ''
            
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
        
        row_style = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial'})
        format_label = workbook.add_format({'font':'Arial', 'font_size': 13, 'valign': 'top', 'bold': True, 'left': True, 'right': True, 'text_wrap':True})
        format_label_qty = workbook.add_format({'font':'Arial', 'font_size': 13, 'valign': 'bottom', 'bold': True, 'left': True, 'right': True, 'text_wrap':True})
        merge_format = workbook.add_format({'align': 'center'})
        merge_format_ = workbook.add_format({'align': 'bottom'})
        _range = len(report_data)
        
        sheet.merge_range(1, 0, _range, 0, '', merge_format)
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
        

        test_shade = ''
        
        shade_range = 0
        shade_range_tot = 0
        # row_ = 1
        # for li in report_data:
        #     for ind, x in enumerate(report_data, start = row):
        #         if x[9] == li[9]:
        #             shade_range += 1
        #         else:
        #             shade_range_tot = shade_range
        #             shade_range = 0
        #             break
        #     sheet.merge_range(1, 9, shade_range_tot, 9, '', merge_format)
        #     row_ +=1
        
        for line in report_data:
            s_t = False
            for x in report_data[row:]:#enumerate(report_data, start = row):
                # if row == 32:
                #     raise UserError((row,_range,shade_range,x[9]))
                last_one = row
                if x[9] == line[9]:
                    shade_range += 1
                else:
                    # shade_range_tot = shade_range
                    # shade_range = 0
                    sheet.merge_range(row, 9, shade_range + 1, 9, '', merge_format)
                    sheet.merge_range(row, 16, shade_range + 1, 16, '', merge_format_)
                    s_t = True
                    shade_range = row
                    
                    break
                if _range == shade_range +1:
                    sheet.merge_range(last_one, 9, shade_range + 1, 9, '', merge_format)
                    sheet.merge_range(last_one, 16, shade_range + 1, 16, '', merge_format_)
                    s_t = True

            #filtered_shade = [x for x in report_data if (x[1] == line[1] or x[1] == '') and x[9] == line[9]]
            #shade_range = len(filtered_shade)

            
            #sheet.merge_range(1, 16, shade_range_tot-1, 16, '', merge_format_)
            
            col=0
            for l in line:
                if col in(0,4,5,6,7,8,9):
                    sheet.write(row, col, l, format_label)
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