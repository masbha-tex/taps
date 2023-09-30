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
    _name = 'report.taps_manufacturing.report_dye_plan_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for ppc'
    
    def generate_xlsx_report(self, workbook, data, planids):
        plan_date = 'Date: '+ str(planids[0].action_date.strftime("%d-%m-%Y"))
        capacities = planids.mapped('capacity')
        capacities = list(set(capacities))
        
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top', 'bold': True, 'align': 'center'})
        merge_format_ = workbook.add_format({'align': 'bottom', 'bold': True})
        
        for m_capa in capacities:
            mc_name = str(m_capa) +'kgs MC Plan'
            fl_planids = planids.filtered(lambda pr: pr.capacity == m_capa)
            sheet = workbook.add_worksheet(mc_name[:41])
            sheet.merge_range(0, 0, 0, 6, mc_name, merge_format)
            sheet.merge_range(0, 13, 0, 17, 'Dyeing Production Plan Report', merge_format)
            sheet.merge_range(1, 0, 1, 6, plan_date, merge_format)
            sheet.merge_range(1, 13, 1, 17, 'Rec/Dye/PPR/006,Rev/00', merge_format)
            
            sheet.write(2, 0, "OA NO", column_style)
            sheet.write(2, 1, "PLAN DATE", column_style)
            sheet.write(2, 2, "ORD REL", column_style)
            sheet.write(2, 3, "CUSTOMER", column_style)
            sheet.write(2, 4, "BUYER", column_style)
            sheet.write(2, 5, "MATERIAL", column_style)
            sheet.write(2, 6, "SHADE", column_style)
            sheet.write(2, 7, "SHADE REF", column_style)
            sheet.write(2, 8, "Qty(kgs)", column_style)
            sheet.write(2, 9, "Dye(kgs)", column_style)
            sheet.write(2, 10, "Run", column_style)
            sheet.write(2, 11, "Ok", column_style)
            sheet.write(2, 12, "Add", column_style)
            sheet.write(2, 13, "H/S", column_style)
            sheet.write(2, 14, "QA", column_style)
            sheet.write(2, 15, "Dis", column_style)
            sheet.write(2, 16, "Pend(kgs)", column_style)
            sheet.write(2, 17, "Remarks", column_style)
            
            machines = fl_planids.mapped('machine_no')
    
            row = 2
            for m in machines:
                m_plan = fl_planids.filtered(lambda pr: pr.machine_no.id == m.id)
                sheet.merge_range(row, 0, row, 17, m.name, merge_format)
                row += 1
                sheet.write(row, 0, "OA NO", column_style)
                sheet.write(row, 1, "PLAN DATE", column_style)
                sheet.write(row, 2, "ORD REL", column_style)
                sheet.write(row, 3, "CUSTOMER", column_style)
                sheet.write(row, 4, "BUYER", column_style)
                sheet.write(row, 5, "MATERIAL", column_style)
                sheet.write(row, 6, "SHADE", column_style)
                sheet.write(row, 7, "SHADE REF", column_style)
                sheet.write(row, 8, "Qty(kgs)", column_style)
                sheet.write(row, 9, "Dye(kgs)", column_style)
                sheet.write(row, 10, "Run", column_style)
                sheet.write(row, 11, "Ok", column_style)
                sheet.write(row, 12, "Add", column_style)
                sheet.write(row, 13, "H/S", column_style)
                sheet.write(row, 14, "QA", column_style)
                sheet.write(row, 15, "Dis", column_style)
                sheet.write(row, 16, "Pend(kgs)", column_style)
                sheet.write(row, 17, "Remarks", column_style)
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


