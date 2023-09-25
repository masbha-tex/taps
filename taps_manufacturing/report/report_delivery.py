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


class ReportDyePlan(models.AbstractModel):
    _name = 'report.taps_manufacturing.report_delivery_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for fg store'
    
    def generate_xlsx_report(self, workbook, data, del_ids):
        # raise UserError (del_ids.default_search_id)
        # self.env['operation.details'].search([('id','in',del_ids)])
        # operations = self.env['operation.details'].search([('id','in',del_ids.ids)])
        mc_name = str(del_ids[0].capacity) + 'kgs MC Plan'
        title_text = del_ids[0].company_id.partner_id.street
        title_text = "\n".join([title_text,'CARTON WISE PACKING DETAILS'])
        title_text = "\n".join([title_text,'DELIVERY DATE : '+ str(del_ids[0].action_date.strftime("%d-%m-%Y"))])
        exporter = del_ids[0].company_id.partner_id.street
        exporter = "\n".join([exporter,del_ids[0].company_id.partner_id.street2+ del_ids[0].company_id.partner_id.city+' '+ del_ids[0].company_id.partner_id.zip])
        exporter = "\n".join([exporter,del_ids[0].company_id.partner_id.country_id.name])

        buyer = 'BUYER: '+del_ids[0].buyer_name
        customer = 'CUSTOMER: '+del_ids[0].partner_id.name
        style_ref = ''
        invoice_no = 'INVOICE NO: '+del_ids[0].mrp_delivery.name
        oa_no = 'OA NO: '+del_ids[0].oa_id.name
        po_no = 'PO NO: '+del_ids[0].oa_id.po_no
        pi_no = 'PI NO: '+del_ids[0].oa_id.pi_number
        item_name = del_ids[0].item + del_ids[0].finish + del_ids[0].slidercodesfg
        
        machines = del_ids.mapped('machine_no')
        report_name = 'Delivery Report'#orders.name
        # for m in machines:
        #     raise UserError((m.name))

        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top', 'bold': True, 'align': 'center'})
        merge_format_ = workbook.add_format({'align': 'bottom', 'bold': True})

# buyer
# customer
# style_ref

        sheet.merge_range(0, 0, 2, 1, exporter, merge_format)
        
        sheet.merge_range(0, 2, 2, 5, title_text, merge_format)
        
        sheet.merge_range(0, 6, 0, 8, buyer, merge_format)
        sheet.merge_range(1, 6, 1, 8, customer, merge_format)
        sheet.merge_range(2, 6, 2, 8, style_ref, merge_format)
        
        sheet.merge_range(3, 0, 3, 1, invoice_no, merge_format)
        sheet.merge_range(4, 0, 4, 1, oa_no, merge_format)

        sheet.merge_range(3, 2, 4, 5, item_name, merge_format)
        
        sheet.merge_range(3, 6, 3, 8, po_no, merge_format)
        sheet.merge_range(4, 6, 4, 8, pi_no, merge_format)
        
        sheet.write(5, 0, "CTN NO", column_style)
        sheet.write(5, 1, "SHADE", column_style)
        sheet.write(5, 2, "SIZE", column_style)
        sheet.write(5, 3, "PCS IN PACKET", column_style)
        sheet.write(5, 4, "NO OF PACKET", column_style)
        sheet.write(5, 5, "TOTAL QTY (pcs)", column_style)
        sheet.write(5, 6, "CARTON TOTAL (pcs)", column_style)
        sheet.write(5, 7, "GROSS WEIGHT (kgs)", column_style)
        sheet.write(5, 8, "NET WEIGHT (kgs)", column_style)


        row = 2
        for m in machines:
            m_plan = del_ids.filtered(lambda pr: pr.machine_no.id == m.id)
            sheet.merge_range(row, 0, row, 17, m.name, merge_format)
            row += 1
            row += 1
            order_data = []
            report_data = []
            for pl in m_plan:
                order_data = []
                order_data = [
                    pl.oa_id.name,
                    pl.action_date,
                    pl.date_order,
                    pl.partner_id.name,
                    pl.buyer_name,
                    pl.fg_categ_type,
                    pl.shade,'',pl.qty,'','','','','','','','',''
                    ]
                report_data.append(order_data)
            for line in report_data:
                col = 0
                for l in line:
                    sheet.write(row, col, l, _row_style)
                    col += 1
                row += 1


