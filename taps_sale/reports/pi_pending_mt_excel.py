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
    _name = 'report.taps_sale.report_pi_pending_mt_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for Pi Pending MT'
    
    def generate_xlsx_report(self, workbook, data, orders):
        report_name = orders.name
        
        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 12})
        
        row_style = workbook.add_format({'font_size': 12, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'center', 'text_wrap':True})#

        sheet.write(0, 0, "OA", column_style)
        sheet.write(0, 1, "EDD", column_style)
        sheet.write(0, 2, "OA DATE", column_style)
        sheet.write(0, 3, "PI", column_style)
        sheet.write(0, 4, "CUSTOMER ", column_style)
        sheet.write(0, 5, "BUYER", column_style)
        sheet.write(0, 6, "STATUS", column_style)
        sheet.write(0, 7, "LOGO", column_style)
        sheet.write(0, 8, "ITEMS", column_style)
        sheet.write(0, 9, "SIZE", column_style)
        sheet.write(0, 10, "MATERIAL( ALLOY / BRASS)", column_style)
        sheet.write(0, 11, "ITEM CATEGORY", column_style)
        sheet.write(0, 12, "FINISH", column_style)
        sheet.write(0, 13, "FINISH CATEGORY", column_style)
        sheet.write(0, 14, "B PART", column_style)
        sheet.write(0, 15, "QTY", column_style)
        sheet.write(0, 16, "PENDING", column_style)
        col = 0
        row = 1
        
        docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
        
        for o_data in docs:
            col = 0
            for l in range(17):
                if col == 0:
                    sheet.write(row, col, orders.name, row_style)
                elif col == 1:
                    sheet.write(row, col, orders.expected_date.strftime("%d/%m/%Y"), row_style)
                elif col == 2:
                    sheet.write(row, col, orders.create_date.strftime("%d/%m/%Y"), row_style)
                elif col == 3:
                    sheet.write(row, col, orders.order_ref.pi_number, row_style)
                elif col == 4:
                    sheet.write(row, col, orders.partner_id.name, row_style)
                elif col == 5:
                    sheet.write(row, col, orders.buyer_name.name, row_style)
                elif col == 6:
                    sheet.write(row, col, '', row_style)
                elif col == 7:
                    sheet.write(row, col, o_data.logo, row_style)
                elif col == 8:
                    sheet.write(row, col, o_data.product_template_id.name, row_style)
                elif col == 9:
                    sheet.write(row, col, o_data.sizemm, row_style)
                elif col == 10:
                    sheet.write(row, col, '', row_style)
                elif col == 11:
                    sheet.write(row, col, '', row_style)
                elif col == 12:
                    sheet.write(row, col, o_data.finish, row_style)
                elif col == 13:
                    sheet.write(row, col, '', row_style)
                elif col == 14:
                    sheet.write(row, col, o_data.b_part, row_style)
                elif col == 15:
                    sheet.write(row, col, o_data.product_uom_qty, row_style)
                elif col == 16:
                    sheet.write(row, col, o_data.product_uom_qty, row_style)
                col += 1
            row += 1
        # sheet.write(row, 15, '=SUM(P{0}:P{1})'.format(2, row), row_style)
        # sheet.write(row, 16, '=SUM(Q{0}:Q{1})'.format(2, row), row_style)
        
        