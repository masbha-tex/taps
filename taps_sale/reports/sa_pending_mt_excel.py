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
    _name = 'report.taps_sale.report_sa_pending_mt_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for Pi Pending MT'
    

    
    def generate_xlsx_report(self, workbook, data, orders):
        report_name = orders.name

        
       

        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 12})
        
        row_style = workbook.add_format({'font_size': 12, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'center', 'text_wrap':True})#

        sheet.write(0, 0, "STATUS", column_style)
        sheet.write(0, 1, "A.D.D", column_style)
        sheet.write(0, 2, "E.D.D", column_style)
        sheet.write(0, 3, "SA NO.", column_style)
        sheet.write(0, 4, "LINE ", column_style)
        sheet.write(0, 5, "SA DATE", column_style)
        sheet.write(0, 6, "PRODUCT CODE", column_style)
        sheet.write(0, 7, "ITEMS", column_style)
        sheet.write(0, 8, "SIZE", column_style)
        sheet.write(0, 9, "STYLE REF", column_style)
        sheet.write(0, 10, "SHAPE", column_style)
        sheet.write(0, 11, "LOGO", column_style)
        sheet.write(0, 12, "LOGO REF", column_style)
        sheet.write(0, 13, "LOGO TYPE", column_style)
        sheet.write(0, 14, "FINISH", column_style)
        sheet.write(0, 15, "FINISH REF", column_style)
        sheet.write(0, 16, "B PART", column_style)
        sheet.write(0, 17, "C PART", column_style)
        sheet.write(0, 18, "D PART", column_style)
        sheet.write(0, 19, "QTY", column_style)
        sheet.write(0, 20, "BUYER", column_style)
        sheet.write(0, 21, "CUSTOMER", column_style)
        sheet.write(0, 22, "PRODUCT TYPE", column_style)
        sheet.write(0, 23, "SUPPLY CHAIN", column_style)
        sheet.write(0, 24, "SEASON", column_style)
        sheet.write(0, 25, "PRIORITY", column_style)
        sheet.write(0, 26, "WASHING TYPE", column_style)
        sheet.write(0, 27, "B,C,D PART FINISH", column_style)
        sheet.write(0, 28, "OTHER REQUIREMENTS", column_style)
        sheet.write(0, 29, "SALES PERSON", column_style)
        
        
        col = 0
        row = 1
        
        docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
        
        for o_data in docs:
            col = 0
            for l in range(30):
                if col == 0:
                    sheet.write(row, col, '', row_style)
                elif col == 1:
                    sheet.write(row, col, orders.create_date.strftime("%d/%m/%Y"), row_style)
                elif col == 2:
                    if orders.commitment_date:
                        sheet.write(row, col, orders.commitment_date.strftime("%d/%m/%Y"), row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 3:
                    sheet.write(row, col, orders.name, row_style)
                elif col == 4:
                    sheet.write(row, col,'', row_style)
                elif col == 5:
                    sheet.write(row, col, orders.create_date.strftime("%d/%m/%Y"), row_style)
                elif col == 6:
                    sheet.write(row, col, o_data.product_code, row_style)
                elif col == 7:
                    sheet.write(row, col, o_data.product_template_id.name, row_style)
                elif col == 8:
                    sheet.write(row, col, (str(o_data.sizemm)+" MM"), row_style)
                elif col == 9:
                    sheet.write(row, col, orders.style_ref, row_style)
                elif col == 10:
                    sheet.write(row, col, o_data.shape, row_style)
                elif col == 11:
                    sheet.write(row, col, o_data.logo, row_style)
                elif col == 12:
                    sheet.write(row, col, o_data.logoref, row_style)
                elif col == 13:
                    sheet.write(row, col, o_data.logo_type, row_style)
                elif col == 14:
                    sheet.write(row, col, o_data.finish, row_style)
                elif col == 15:
                    sheet.write(row, col, o_data.finish_ref, row_style)
                elif col == 16:
                    sheet.write(row, col, o_data.b_part, row_style)
                elif col == 17:
                    sheet.write(row, col, o_data.c_part, row_style)
                elif col == 18:
                    sheet.write(row, col, o_data.d_part, row_style)
                elif col == 19:
                    sheet.write(row, col,(o_data.product_uom_qty), row_style)
                elif col == 20:
                    sheet.write(row, col, orders.buyer_name.name, row_style)
                elif col == 21:
                    sheet.write(row, col, orders.partner_id.name, row_style)
                elif col == 22:
                    sheet.write(row, col, orders.production_type, row_style)
                elif col == 23:
                    sheet.write(row, col, orders.supply_chain, row_style)
                elif col == 24:
                    sheet.write(row, col, orders.season, row_style)
                elif col == 25:
                    sheet.write(row, col, orders.priority, row_style)
                elif col == 26:
                    sheet.write(row, col, orders.washing_type, row_style)
                elif col == 27:
                    sheet.write(row, col, orders.bcd_part_finish, row_style)
                elif col == 28:
                    sheet.write(row, col, orders.remarks, row_style)
                elif col == 29:
                    sheet.write(row, col, orders.sale_representative.name, row_style)
                col += 1
            row += 1
        # sheet.write(row, 15, '=SUM(P{0}:P{1})'.format(2, row), row_style)
        # sheet.write(row, 16, '=SUM(Q{0}:Q{1})'.format(2, row), row_style)
        # return report
        