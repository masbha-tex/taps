import base64
import pytz

import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
import re
import math
_logger = logging.getLogger(__name__)

class SalesReport(models.TransientModel):
    _name = 'sale.pdf.report'
    _description = 'All Sales Report'    

    
    date_from = fields.Datetime('Date from', required=True, default=lambda self: (fields.Datetime.now()))
    date_to = fields.Datetime('Date to', required=True, default=lambda self: (fields.Datetime.now()))
    report_type = fields.Selection([
        ('orderacc','Order Acceptance'),
        ('pi',	'PI'),
        ('oa',	'OA'),
        ('sa',	'SA'),],
        string='Report Type', required=True,
        help='By Salary Head Wise Report', default='orderacc')
    
    mode_company_id = fields.Many2one('res.company',  string='Company Mode', readonly=False, required=True, default=lambda self: self.env.company.id)

    file_data = fields.Binary(readonly=True, attachment=False)


    def action_generate_xlsx_report(self):
        
        data = {'date_from': self.date_from, 
                'date_to': self.date_to, 
                'mode_company_id': self.mode_company_id.id,
                'report_type': self.report_type,
                }
        if self.report_type == 'orderacc' and data.get('mode_company_id') == 1:
            return self.order_acceptance_xls(self, data=data)
        if self.report_type == 'orderacc' and data.get('mode_company_id') == 3:
            return self.order_acceptance_xls_mt(self, data=data)

    def order_acceptance_xls(self,docids,data):
        start_time = fields.datetime.now()
        domain = []
        if data.get('date_from'):
            domain.append(('date_order', '>=',data.get("date_from")))
        if data.get('date_to'):
            domain.append(('date_order', '<=',data.get("date_to")))
        if data.get('mode_company_id'):
            domain.append(('company_id', '=', data.get('mode_company_id')))

        domain.append(('sales_type', '=', 'oa'))
        domain.append(('state', '=', 'sale'))
        domain.append('|')
        domain.append(('pi_type', '=', 'regular'))
        domain.append(('pi_type', '=', 'replacement'))
        docs = self.env['sale.order'].search(domain).sorted(key = 'id', reverse=False)
        # raise UserError((domain))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, })
        report_title_style_2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 13, })
        worksheet.merge_range('A1:F1',  'ORDER ACCEPTANCE', report_title_style)
        worksheet.merge_range('A2:F2',  'From : ' + str(data.get('date_from').strftime('%d-%m-%Y')), report_title_style_2)
        worksheet.merge_range('A3:F3',  'To :   ' + str(data.get('date_to').strftime('%d-%m-%Y')), report_title_style_2)
        worksheet.merge_range('A4:F4',  'Unit : Zipper', report_title_style_2)

        
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

        worksheet.set_column(3,3,15)
        worksheet.set_column(0,0,25)
        worksheet.set_column(1,1,20)
        worksheet.set_column(2,2,30)
        worksheet.set_column(4,4,40)
        worksheet.set_column(5,5,25)
        worksheet.set_column(7,7,30)
        worksheet.set_column(8,9,25)
        worksheet.set_column(10,11,10)
        worksheet.set_column(12,13,14)
        worksheet.set_column(14,16,14)
        worksheet.set_column(17,17,20)
        worksheet.set_column(19,20,20)
        worksheet.write(5, 0, 'Sales Representative',column_issued_style)
        worksheet.write(5, 1, 'Sales Team',column_issued_style)
        worksheet.write(5, 2, 'Team leader',column_issued_style)
        worksheet.write(5, 3, 'Date',column_issued_style)
        worksheet.write(5, 4, 'Customer',column_issued_style)
        worksheet.write(5, 5, 'Buyer',column_issued_style)
        worksheet.write(5, 6, 'SL',column_issued_style)
        worksheet.write(5, 7, 'Product',column_issued_style)
        worksheet.write(5, 8, 'Finish',column_issued_style)
        worksheet.write(5, 9, 'Slider',column_issued_style)
        worksheet.write(5, 10, 'PI',column_issued_style)
        worksheet.write(5, 11, 'OA',column_issued_style)
        worksheet.write(5, 12, 'Avg Size INCH',column_issued_style)
        worksheet.write(5, 13, 'Avg Size CM',column_issued_style)
        worksheet.write(5, 14, 'Quantity(Pcs)',column_issued_style)
        worksheet.write(5, 15, 'Value($)',column_issued_style)
        worksheet.write(5, 16, 'Avg Price($)/Pcs',column_issued_style)
        worksheet.write(5, 17, 'Payment Terms',column_issued_style)
        worksheet.write(5, 18, 'Type',column_issued_style)
        worksheet.write(5, 19, 'Tape Weight(kg)',column_issued_style)
        worksheet.write(5, 20, 'Metal Weight(kg)',column_issued_style)
        row=6
        col=0
        serial= 0
        for l in docs:
            serial += 1
            if col == 0:
                worksheet.write(row, col, l.user_id.partner_id.name,column_title_style)
                col += 1
            if col == 1:
                worksheet.write(row, col, l.team_id.name,column_title_style)
                col += 1
            if col == 2:
                worksheet.write(row, col, l.team_id.user_id.partner_id.name,column_title_style)
                col += 1
            if col == 3:
                worksheet.write(row, col, l.date_order,date_format)
                col += 1
            if col == 4:
                worksheet.write(row, col, l.partner_id.name,column_title_style)
                col += 1
            if col == 5:
                worksheet.write(row, col, l.buyer_name.name,column_title_style)
                col += 1
            if col == 6:
                
                worksheet.write(row, col, serial,column_title_style_2)
                col += 1
            if col == 7:
                worksheet.write(row, col, l.order_line[0].product_template_id.name,column_title_style)
                col += 1
            if col == 8:
                if l.order_line[0].finish != 'TBA':
                    worksheet.write(row, col, l.order_line[0].finish,column_title_style)
                    col += 1
                if l.order_line[0].finish == 'TBA':
                    worksheet.write(row, col, '',column_title_style)
                    col += 1
            if col == 9:
                if l.order_line[0].slidercodesfg != 'TBA':
                    worksheet.write(row, col, l.order_line[0].slidercodesfg,column_title_style)
                    col += 1
                if l.order_line[0].slidercodesfg == 'TBA':
                    worksheet.write(row, col, '',column_title_style)
                    col += 1
            if col == 10:
                worksheet.write(row, col, l.order_ref.pi_number,column_title_style)
                col += 1
            if col == 11:
                worksheet.write(row, col, l.name,column_title_style)
                col += 1
            if col == 12:
                if l.order_line[0].sizein != "N/A":
                    worksheet.write(row, col, l.avg_size,column_title_style)
                    col += 1
                if l.order_line[0].sizein == "N/A":
                    worksheet.write(row, col, '--',column_title_style)
                    col += 1
            if col == 13:
                if l.order_line[0].sizecm != "N/A":
                    worksheet.write(row, col, l.avg_size,column_title_style)
                    col += 1
                if l.order_line[0].sizecm == "N/A":
                    worksheet.write(row, col, '--',column_title_style)
                    col += 1
            if col == 14:
                worksheet.write(row, col, l.total_product_qty,column_title_style)
                col += 1
            if col == 15:
                worksheet.write(row, col, l.amount_total,column_title_style)
                col += 1
            if col == 16:
                worksheet.write(row, col, l.avg_price,column_title_style)
                col += 1
            if col == 17:
                worksheet.write(row, col, l.payment_term_id.name,column_title_style)
                col += 1
            if col == 18:
                worksheet.write(row, col, l.pi_type,column_title_style)
                col += 1
            if col == 19:
                worksheet.write(row, col, (sum(item.tape_con for item in l.order_line)),column_title_style)
                col += 1
            if col == 20:
                worksheet.write(row, col, (sum(item.wire_con for item in l.order_line)),column_title_style)
                col = 0
                row +=1
                
            
            # col +=1

        # worksheet.write(row, 6, '=SUM(G{0}:G{1})'.format(6, row), column_title_style_2)
        worksheet.write(row, 14, '=SUM(O{0}:O{1})'.format(6, row), column_issued_style)
        worksheet.write(row, 15, '=SUM(P{0}:P{1})'.format(6, row), column_issued_style)
        worksheet.write(row, 19, '=SUM(T{0}:T{1})'.format(6, row), column_issued_style)
        worksheet.write(row, 20, '=SUM(U{0}:U{1})'.format(6, row), column_issued_style)
        
        workbook.close()
        output.seek(0)
        # binary_data = output.getvalue()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Order Acceptance')),
            'target': 'self',
        }









    
    def order_acceptance_xls_mt(self,docids,data):
            start_time = fields.datetime.now()
            domain = []
            if data.get('date_from'):
                domain.append(('order_id.date_order', '>=',data.get("date_from")))
            if data.get('date_to'):
                domain.append(('order_id.date_order', '<=',data.get("date_to")))
            if data.get('mode_company_id'):
                domain.append(('company_id', '=', data.get('mode_company_id')))
    
            domain.append(('order_id.sales_type', '=', 'oa'))
            domain.append(('order_id.state', '=', 'sale'))
            domain.append(('product_template_id.name','!=', 'MOULD'))
            domain.append('|')
            domain.append(('order_id.pi_type', '=', 'regular'))
            domain.append(('order_id.pi_type', '=', 'replacement'))
            docs = self.env['sale.order.line'].search(domain).sorted(key = 'id', reverse=False)
            # raise UserError((domain))
    
            output = io.BytesIO()
            workbook = xlsxwriter.Workbook(output, {'in_memory': True})
            worksheet = workbook.add_worksheet()
            report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, })
            report_title_style_2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 13 })
            worksheet.merge_range('A1:F1',  'ORDER ACCEPTANCE', report_title_style)
            worksheet.merge_range('A2:F2',  'From : ' + str(data.get('date_from').strftime('%d-%m-%Y')), report_title_style_2)
            worksheet.merge_range('A3:F3',  'To :   ' + str(data.get('date_to').strftime('%d-%m-%Y')), report_title_style_2)
            worksheet.merge_range('A4:F4',  'Unit : Metal Trims', report_title_style_2)
            
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
    
            worksheet.set_column(3,3,15)
            worksheet.set_column(0,0,25)
            worksheet.set_column(1,1,20)
            worksheet.set_column(2,2,30)
            worksheet.set_column(4,4,40)
            worksheet.set_column(5,5,25)
            worksheet.set_column(7,7,30)
            worksheet.set_column(8,9,25)
            worksheet.set_column(10,11,10)
            worksheet.set_column(12,15,18)
            worksheet.set_column(16,16,14)
           
            worksheet.write(5, 0, 'Sales Representative',column_issued_style)
            worksheet.write(5, 1, 'Sales Team',column_issued_style)
            worksheet.write(5, 2, 'Team leader',column_issued_style)
            worksheet.write(5, 3, 'Date',column_issued_style)
            worksheet.write(5, 4, 'Customer',column_issued_style)
            worksheet.write(5, 5, 'Buyer',column_issued_style)
            worksheet.write(5, 6, 'SL',column_issued_style)
            worksheet.write(5, 7, 'Product',column_issued_style)
            worksheet.write(5, 8, 'Finish',column_issued_style)
            worksheet.write(5, 9, 'PI',column_issued_style)
            worksheet.write(5, 10, 'OA',column_issued_style)
            worksheet.write(5, 11, 'Size (MM)',column_issued_style)
            worksheet.write(5, 12, 'Quantity(Gross)',column_issued_style)
            worksheet.write(5, 13, 'Value($)',column_issued_style)
            worksheet.write(5, 14, 'Avg Price($)/Gross',column_issued_style)
            worksheet.write(5, 15, 'Payment Terms',column_issued_style)
            worksheet.write(5, 16, 'Type',column_issued_style)
    
            row=6
            col=0
            serial= 0
            for l in docs:
                
                serial += 1
                if col == 0:
                    worksheet.write(row, col, l.order_id.user_id.partner_id.name,column_title_style)
                    col += 1
                if col == 1:
                    worksheet.write(row, col, l.order_id.team_id.name,column_title_style)
                    col += 1
                if col == 2:
                    worksheet.write(row, col, l.order_id.team_id.user_id.partner_id.name,column_title_style)
                    col += 1
                if col == 3:
                    worksheet.write(row, col, l.order_id.date_order,date_format)
                    col += 1
                if col == 4:
                    worksheet.write(row, col, l.order_id.partner_id.name,column_title_style)
                    col += 1
                if col == 5:
                    worksheet.write(row, col, l.order_id.buyer_name.name,column_title_style)
                    col += 1
                if col == 6:
                    
                    worksheet.write(row, col, serial,column_title_style_2)
                    col += 1
                if col == 7:
                    worksheet.write(row, col, l.product_template_id.name,column_title_style)
                    col += 1
                if col == 8:
                    worksheet.write(row, col, l.finish,column_title_style)
                    col += 1
                # if col == 9:
                #     worksheet.write(row, col, "TZP-"+ str(l.order_line[0].slidercodesfg.split('-')[1]),column_title_style)
                #     col += 1
                if col == 9:
                    worksheet.write(row, col, l.order_id.order_ref.pi_number,column_title_style)
                    col += 1
                if col == 10:
                    worksheet.write(row, col, l.order_id.name,column_title_style)
                    col += 1
                # if col == 12:
                #     if l.order_line[0].sizein != "N/A":
                #         worksheet.write(row, col, l.avg_size,column_title_style)
                #         col += 1
                #     if l.order_line[0].sizein == "N/A":
                #         worksheet.write(row, col, '--',column_title_style)
                #         col += 1
                if col == 11:
                    if l.sizemm != "N/A":
                        worksheet.write(row, col, float(l.sizemm),column_title_style)
                        col += 1
                    if l.sizemm == "N/A":
                        worksheet.write(row, col, '--',column_title_style)
                        col += 1
                if col == 12:
                    worksheet.write(row, col, l.product_uom_qty,column_title_style)
                    col += 1
                if col == 13:
                    worksheet.write(row, col, l.price_subtotal,column_title_style)
                    col += 1
                if col == 14:
                    worksheet.write(row, col, l.order_id.avg_price,column_title_style)
                    col += 1
                if col == 15:
                    worksheet.write(row, col, l.order_id.payment_term_id.name,column_title_style)
                    col += 1
                if col == 16:
                    worksheet.write(row, col, l.order_id.pi_type,column_title_style)
                    col = 0
                    row +=1
                
                
            worksheet.write(row, 12, '=SUM(M{0}:M{1})'.format(6, row), column_issued_style)
            worksheet.write(row, 13, '=SUM(N{0}:N{1})'.format(6, row), column_issued_style)
    
            
            
            workbook.close()
            output.seek(0)
            # binary_data = output.getvalue()
            xlsx_data = output.getvalue()
            #raise UserError(('sfrgr'))
            
            self.file_data = base64.encodebytes(xlsx_data)
            end_time = fields.datetime.now()
            _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Order Acceptance')),
                'target': 'self',
            }



