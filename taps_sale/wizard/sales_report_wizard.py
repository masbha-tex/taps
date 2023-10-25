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
    
    mode_company_id = fields.Many2one('res.company',  string='Company Mode', readonly=False)

    file_data = fields.Binary(readonly=True, attachment=False)


    def action_generate_xlsx_report(self):
        
        data = {'date_from': self.date_from, 
                'date_to': self.date_to, 
                'mode_company_id': self.mode_company_id.id,
                'report_type': self.report_type,
                }
        if self.report_type == 'orderacc':
            return self.order_acceptance_xls(self, data=data)

    def order_acceptance_xls(self,docids,data):
        start_time = fields.datetime.now()
        domain = []
        if data.get('date_from'):
            domain.append(('date_order', '>=',data.get("date_from")))
        if data.get('date_to'):
            domain.append(('date_order', '<=',data.get("date_to")))
        if data.get('mode_company_id'):
            domain.append(('company_id', '=', data['mode_company_id']))

        domain.append(('sales_type', '=', 'oa'))
        docs = self.env['sale.order'].search(domain)
        # raise UserError((domain))

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy HH:MM','align': 'center','bold': True, 'font_size': 9,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FFC000', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 9,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FDE9D9', 'font_size': 12,'left': True, 'top': True, 'right': True, 'bottom': True})
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
        worksheet.set_column(12,16,12)
        worksheet.set_column(17,17,20)
        worksheet.set_column(19,20,15)
        worksheet.write(5, 0, 'Sales Representative',column_issued_style)
        worksheet.write(5, 1, 'Sales Team',column_issued_style)
        worksheet.write(5, 2, 'Team leader',column_issued_style)
        worksheet.write(5, 3, 'Date',column_issued_style)
        worksheet.write(5, 4, 'Customer',column_issued_style)
        worksheet.write(5, 5, 'Buyer',column_issued_style)
        worksheet.write(5, 6, 'Sl',column_issued_style)
        worksheet.write(5, 7, 'Product',column_issued_style)
        worksheet.write(5, 8, 'Finish',column_issued_style)
        worksheet.write(5, 9, 'Slider',column_issued_style)
        worksheet.write(5, 10, 'PI',column_issued_style)
        worksheet.write(5, 11, 'OA',column_issued_style)
        worksheet.write(5, 12, 'Avg Size CM',column_issued_style)
        worksheet.write(5, 13, 'Avg Size INCH',column_issued_style)
        worksheet.write(5, 14, 'Quantity',column_issued_style)
        worksheet.write(5, 15, 'Value',column_issued_style)
        worksheet.write(5, 16, 'Avg Price',column_issued_style)
        worksheet.write(5, 17, 'Payment Terms',column_issued_style)
        worksheet.write(5, 18, 'Type',column_issued_style)
        worksheet.write(5, 19, 'Tape Weight(kg)',column_issued_style)
        worksheet.write(5, 20, 'Metal Weight(kg)',column_issued_style)
        row=6
        col=0
        for l in docs:
            if col == 0: 
                worksheet.write(row, col, l.sale_representative.name,column_title_style)
                col += 1
            if col == 1:
                worksheet.write(row, col, l.sale_representative.team.team_name,column_title_style)
                col += 1
            if col == 2:
                worksheet.write(row, col, l.sale_representative.leader.name,column_title_style)
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
                worksheet.write(row, col, 1,column_title_style)
                col += 1
            if col == 7:
                worksheet.write(row, col, l.order_line[0].product_template_id.name,column_title_style)
                col += 1
            if col == 8:
                worksheet.write(row, col, l.order_line[0].finish.split()[0],column_title_style)
                col += 1
            if col == 9:
                worksheet.write(row, col, "TZP-"+ str(l.order_line[0].slidercodesfg.split('-')[1]),column_title_style)
                col += 1
            if col == 10:
                worksheet.write(row, col, l.order_ref.pi_number,column_title_style)
                col += 1
            if col == 11:
                worksheet.write(row, col, l.name,column_title_style)
                col += 1
            if col == 12:
                worksheet.write(row, col, l.avg_size,column_title_style)
                col += 1
            if col == 13:
                worksheet.write(row, col, l.avg_size,column_title_style)
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



