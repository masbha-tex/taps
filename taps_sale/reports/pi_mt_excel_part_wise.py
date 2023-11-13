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
    _name = 'report.taps_sale.report_pi_mt_part_wise_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for Pi MT'
    
    def generate_xlsx_report(self, workbook, data, orders):
        # report_name = orders.name

        sheet = workbook.add_worksheet("PI_MT_EXCEL_PART_WISE")
        column_style = workbook.add_format({'bold': True, 'font_size': 9})
        
        row_style = workbook.add_format({'font_size': 11, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'middle', 'text_wrap':True})#
        
        # merge_format = workbook.add_format({'align': 'top'})
        # sheet.set_column(9, 9, 40)
        # sheet.merge_range(1, 8, _range, 8, '', merge_format)
        

        sheet.write(0, 0, "OA", column_style)
        sheet.write(0, 1, "OA RELEASE DATE", column_style)
        sheet.write(0, 2, "PI No.", column_style)
        sheet.write(0, 3, "CUSTOMER", column_style)
        sheet.write(0, 4, "BUYER", column_style)
        sheet.write(0, 5, "DELIVERY DATE", column_style)
        sheet.write(0, 6, "PRIORITY", column_style)
        sheet.write(0, 7, "COMPLETION DATE", column_style)
        sheet.write(0, 8, "PRODUCT CODE", column_style)
        sheet.write(0, 9, "ITEM DESCRIPTION", column_style)
        sheet.write(0, 10, "SIZE", column_style)
        sheet.write(0, 11, "SHAPE", column_style)
        sheet.write(0, 12, "LOGO", column_style)
        sheet.write(0, 13, "LOGO REF", column_style)
        sheet.write(0, 14, "LOGO TYPE", column_style)
        sheet.write(0, 15, "FINISH", column_style)
        sheet.write(0, 16, "FINISH REF", column_style)
        sheet.write(0, 17, "B PART", column_style)
        sheet.write(0, 18, "C PART", column_style)
        sheet.write(0, 19, "D PART", column_style)
        sheet.write(0, 20, "QTY", column_style)
        sheet.write(0, 21, "STYLE", column_style)
        sheet.write(0, 22, "SEARCH", column_style)
        col = 0
        row = 1
        list = orders.mapped('id')
        docs = self.env['sale.order.line'].search([('order_id', 'in', list)])
        docs = sorted(docs, key=lambda r: r.order_id.id, reverse=False)
        for o_data in docs:
            col = 0
        
            
            for l in range(24):
                
                if col == 0:
                    sheet.write(row, col, o_data.order_id.name, row_style)
                elif col == 1:
                    sheet.write(row, col, o_data.order_id.create_date.strftime("%d/%m/%Y"), row_style)
                elif col == 2:
                    sheet.write(row, col, o_data.order_id.order_ref.pi_number, row_style)
                elif col == 3:
                    sheet.write(row, col, o_data.order_id.partner_id.name, row_style)
                elif col == 4:
                    sheet.write(row, col, o_data.order_id.buyer_name.name, row_style)
                elif col == 5:
                    sheet.write(row, col, o_data.order_id.expected_date.strftime("%d/%m/%Y"), row_style)
                elif col == 6:
                    sheet.write(row, col, '', row_style)
                elif col == 7:
                    sheet.write(row, col, '', row_style)
                elif col == 8:
                    if o_data.product_code:
                        sheet.write(row, col, o_data.product_code, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 9:
                    sheet.write(row, col, o_data.product_template_id.name, row_style)
                elif col == 10:
                    sheet.write(row, col, o_data.sizemm, row_style)
                elif col == 11:
                    if o_data.shape:
                        sheet.write(row, col, o_data.shape, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 12:
                    if o_data.logo:
                        sheet.write(row, col, o_data.logo, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 13:
                    if o_data.logoref:
                        sheet.write(row, col, o_data.logoref, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 14:
                    if o_data.logo_type:
                        sheet.write(row, col, o_data.logo_type, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 15:
                    if o_data.finish:
                        sheet.write(row, col, o_data.finish, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 16:
                    if o_data.finish_ref:
                        sheet.write(row, col, o_data.finish_ref, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 17:
                    if o_data.b_part:
                        sheet.write(row, col, o_data.b_part, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 18:
                    if o_data.c_part:
                        sheet.write(row, col, o_data.c_part, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 19:
                    if o_data.d_part:
                        sheet.write(row, col, o_data.d_part, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 20:
                    sheet.write(row, col, o_data.product_uom_qty, row_style)
                elif col == 21:
                    if o_data.style:
                        sheet.write(row, col, o_data.style, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 22:
                    sheet.write(row, col, '', row_style)
                
                col += 1
            row += 1
                
        # sheet.write(row, 15, '=SUM(P{0}:P{1})'.format(2, row), row_style)
        # sheet.write(row, 16, '=SUM(Q{0}:Q{1})'.format(2, row), row_style)
                
            
        