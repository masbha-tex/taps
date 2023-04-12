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
    
    
    def generate_xlsx_report(self, workbook, data, orders):
        
        
        report_name = orders.name
        sheet = workbook.add_worksheet(report_name[:41])
        bold = workbook.add_format({'bold': True})
        sheet.write(1, 1, "PRODUCT", bold)
        sheet.write(1, 2, "SLIDER CODE", bold)
        sheet.write(1, 3, "FINISH", bold)
        sheet.write(1, 4, "PI NO", bold)
        sheet.write(1, 5, "OA DATE", bold)
        sheet.write(1, 6, "DELIVERY DATE", bold)
        sheet.write(1, 7, "SHADE", bold)
        sheet.write(1, 8, "SIZE(INCH)", bold)
        sheet.write(1, 9, "SIZE(CM)", bold)
        sheet.write(1, 10, "QUANTITY", bold)
        sheet.write(1, 11, "TAPE/KG", bold)
        sheet.write(1, 12, "SHADE TOTAL", bold)
        sheet.write(1, 13, "WIRE/KG", bold)
        sheet.write(1, 14, "SLIDER/PCS", bold)
        sheet.write(1, 15, "H-BOTTOM/KG", bold)
        sheet.write(1, 16, "U-TOP/KG", bold)
        sheet.write(1, 17, "PINBOX/KG", bold)
        sheet.write(1, 18, "SALESPERSON", bold)
        col = 1
        row=2
        
        docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
        
        # raise UserError((docs.id))
        
        report_data = []
        order_data = []
        slnumber=0
        for o_data in docs:
            slnumber = slnumber+1
            
            pr_name = o_data.product_template_id.name
            slider = o_data.slidercodesfg
            finish = o_data.finish
            pi_num = orders.order_ref.pi_number
            create_date = orders.create_date.strftime("%d-%m-%Y")
            expected_date = orders.expected_date.strftime("%d-%m-%Y")
            shade = o_data.shade
            shadewise_tape = o_data.shadewise_tape
            
            filtered_name = [x for x in report_data if x[0] == o_data.product_template_id.name]
            if filtered_name:
                pr_name = ''
            
            filtered_slider = [x for x in report_data if (x[0] == o_data.product_template_id.name or x[0] == '') and x[1] == o_data.slidercodesfg]
            if filtered_slider:
                slider = ''

            filtered_finish = [x for x in report_data if (x[0] == o_data.product_template_id.name or x[0] == '') and x[2] == o_data.finish]
            if filtered_finish:
                finish = ''
                
            filtered_pi_num = [x for x in report_data if x[3] == orders.order_ref.pi_number]
            if filtered_pi_num:
                pi_num = ''
            
            filtered_create_date = [x for x in report_data if x[4] == orders.create_date.strftime("%d-%m-%Y")]
            if filtered_create_date:
                create_date = ''
            
            filtered_expected_date = [x for x in report_data if x[5] == orders.expected_date.strftime("%d-%m-%Y")]
            if filtered_expected_date:
                expected_date = ''
            
            filtered_shade = [x for x in report_data if (x[0] == o_data.product_template_id.name or x[0] == '') and x[6] == o_data.shade]
            if filtered_shade:
                shade = ''
                
            filtered_shadewise_tape = [x for x in report_data if (x[0] == o_data.product_template_id.name or x[0] == '') and 
                                       x[6] == o_data.shade and x[11] == o_data.shadewise_tape]
            if filtered_shadewise_tape:
                shadewise_tape = ''
                
            order_data = [
                pr_name,
                slider,
                finish,
                pi_num,
                create_date,
                expected_date,
                shade,
                o_data.sizein,
                o_data.sizecm,
                o_data.product_uom_qty,
                o_data.tape_con,
                shadewise_tape,
                o_data.wire_con,
                o_data.slider_con,
                o_data.botomwire_con,
                o_data.topwire_con,
                o_data.pinbox_con,
                orders.sale_representative.name,
                "",
            ]
            report_data.append(order_data)
        
        # output = io.BytesIO()
        # workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # worksheet = workbook.add_worksheet()
        
        for line in report_data:
            col=1
            for l in line:
                sheet.write(row, col, l)
                col+=1
            row+=1