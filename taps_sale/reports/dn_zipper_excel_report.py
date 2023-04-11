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
        sheet.write(1, 12, "WIRE/KG", bold)
        sheet.write(1, 13, "SLIDER/PCS", bold)
        sheet.write(1, 14, "H-BOTTOM/KG", bold)
        sheet.write(1, 15, "U-TOP/KG", bold)
        sheet.write(1, 16, "PINBOX/KG", bold)
        sheet.write(1, 17, "SALESPERSON", bold)
        col = 1
        row=2
        
        docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
        
        # raise UserError((docs.id))
        
        report_data = []
        order_data = []
        slnumber=0
        for o_data in docs:
            slnumber = slnumber+1
            order_data = [
                o_data.product_template_id.name,
                o_data.slidercodesfg,
                o_data.finish,
                orders.order_ref.pi_number,
                orders.create_date.strftime("%d-%m-%Y"),
                orders.expected_date.strftime("%d-%m-%Y"),
                o_data.shade,
                o_data.sizein,
                o_data.sizecm,
                o_data.product_uom_qty,
                o_data.tape_con,
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