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
    _name = 'report.taps_sale.report_oa_file_mt_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'OA FILE MT"'
    
    def generate_xlsx_report(self, workbook, data, orders):
        # report_name = orders.name

        worksheet = workbook.add_worksheet("OA FILE MT")
        column_style = workbook.add_format({'bold': True, 'font_size': 9})
        
        row_style = workbook.add_format({'font_size': 11, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'middle', 'text_wrap':True})#
        
        # merge_format = workbook.add_format({'align': 'top'})
        # sheet.set_column(9, 9, 40)
        # sheet.merge_range(1, 8, _range, 8, '', merge_format)
        
        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, })
        report_title_style_2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 13, })
        # worksheet.merge_range('A1:F1',  'ORDER ACCEPTANCE', report_title_style)
        # worksheet.merge_range('A2:F2',  'From : ' + str(data.get('date_from').strftime('%d-%m-%Y')), report_title_style_2)
        # worksheet.merge_range('A3:F3',  'To :   ' + str(data.get('date_to').strftime('%d-%m-%Y')), report_title_style_2)
        # worksheet.merge_range('A4:F4',  'Unit : Zipper', report_title_style_2)

        
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy','align': 'center','bold': True, 'font_size': 9,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FFC000', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 9,'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00'})
        column_title_style_2 = workbook.add_format({'align': 'center','bold': True, 'font_size': 9,'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0'})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FDE9D9', 'font_size': 12,'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00'})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})
        row_style = workbook.add_format({'font_size': 11, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_style_1 = workbook.add_format({'font_size': 11, 'font':'Calibri', 'valign': 'right', 'top': True, 'bottom': True})
        format_label_1 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right', 'top': True,  'bottom': True})
        
        format_label_2 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True})
        
        format_label_3 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        
        format_label_4 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right',  'top': True,  'bottom': True, 'bold': True})


        worksheet.set_column(0,3,15)
        worksheet.set_column(4,4,25)
        worksheet.set_column(6,9,15)
        worksheet.set_column(6,9,20)
        worksheet.set_column(10,11,25)
        worksheet.set_column(12,19,25)
        
        worksheet.write(0, 0, "OA", column_issued_style)
        worksheet.write(0, 1, "PI", column_issued_style)
        worksheet.write(0, 2, "OA DATE", column_issued_style)
        worksheet.write(0, 3, "CODE", column_issued_style)
        worksheet.write(0, 4, "ITEM", column_issued_style)
        worksheet.write(0, 5, "SIZE(MM)", column_issued_style)
        worksheet.write(0, 6, "SHAPE", column_issued_style)
        worksheet.write(0, 7, "LOGO", column_issued_style)
        worksheet.write(0, 8, "LOGO REF", column_issued_style)
        worksheet.write(0, 9, "LOGO TYPE", column_issued_style)
        worksheet.write(0, 10, "FINISH", column_issued_style)
        worksheet.write(0, 11, "FINISH REF", column_issued_style)
        worksheet.write(0, 12, "B PART", column_issued_style)
        worksheet.write(0, 13, "C PART", column_issued_style)
        worksheet.write(0, 14, "D PART", column_issued_style)
        worksheet.write(0, 15, "QTY(Pcs)", column_issued_style)
        worksheet.write(0, 16, "QTY(Gross)", column_issued_style)
        worksheet.write(0, 17, "STYLE", column_issued_style)
        worksheet.write(0, 18, "GMT", column_issued_style)
        worksheet.write(0, 19, "MOLD", column_issued_style)
        
        col = 0
        row = 1
        
        list = orders.mapped('id')
        docs = self.env['sale.order.line'].search([('order_id', '=', list)])
        docs = sorted(docs, key=lambda r: r.order_id.id, reverse=False)
        for o_data in docs:
            col = 0
            for l in range(20):
                if col == 0:
                    worksheet.write(row, col, o_data.order_id.name, column_title_style)
                elif col == 1:
                    worksheet.write(row, col, o_data.order_id.order_ref.pi_number, column_title_style)
                elif col == 2:
                    worksheet.write(row, col, o_data.order_id.date_order.strftime("%d/%m/%Y"), column_title_style)
                elif col == 3:
                    worksheet.write(row, col, o_data.product_code, column_title_style)
                elif col == 4:
                    worksheet.write(row, col,o_data.product_template_id.name , column_title_style)
                elif col == 5:
                    worksheet.write(row, col, o_data.sizemm, column_title_style)
                elif col == 6:
                    worksheet.write(row, col, o_data.shape, column_title_style)
                elif col == 7:
                    if o_data.logo:
                        worksheet.write(row, col, o_data.logo, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 8:
                    if o_data.logoref:
                        worksheet.write(row, col, o_data.logoref, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 9:
                    if o_data.logo_type:
                        worksheet.write(row, col, o_data.logo_type, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 10:
                    if o_data.finish:
                        worksheet.write(row, col, o_data.finish, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 11:
                    if o_data.finish_ref:
                        worksheet.write(row, col, o_data.finish_ref, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 12:
                    if o_data.b_part:
                        worksheet.write(row, col, o_data.b_part, column_title_style)
                    else:
                        worksheet.write(row, col,'', column_title_style)
                elif col == 13:
                    if o_data.c_part:
                        worksheet.write(row, col, o_data.c_part, column_title_style)
                    else:
                        worksheet.write(row, col,'', column_title_style)
                elif col == 14:
                    if o_data.d_part:
                        worksheet.write(row, col, o_data.d_part, column_title_style)
                    else:
                        worksheet.write(row, col, '', column_title_style)
                elif col == 15:
                    worksheet.write(row, col, o_data.product_uom_qty*144, column_title_style)
                elif col == 16:
                    worksheet.write(row, col, o_data.product_uom_qty, column_title_style)
                elif col == 17:
                    if o_data.style:
                        worksheet.write(row, col, o_data.style, column_title_style)
                    else:
                        worksheet.write(row, col,'', column_title_style)
                elif col == 18:
                    if o_data.gmt:
                        worksheet.write(row, col, o_data.gmt, column_title_style)
                    else:
                        worksheet.write(row, col,'', column_title_style)
                elif col == 19:
                    if o_data.mold_set:
                        worksheet.write(row, col, o_data.mold_set, column_title_style)
                    else:
                        worksheet.write(row, col,'', column_title_style)
                col += 1
            row += 1
                
        # sheet.write(row, 15, '=SUM(P{0}:P{1})'.format(2, row), row_style)
        # sheet.write(row, 16, '=SUM(Q{0}:Q{1})'.format(2, row), row_style)
                
            
        