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



class DyeingQcBalance(models.AbstractModel):
    _name = 'report.taps_manufacturing.report_dy_qc_balance_xls'
    _inherit = 'report.report_xlsx.abstract'
    _description = 'report for ppc'
    
    def generate_xlsx_report(self, workbook, data, planids):
        plan_date = 'Date: '+ str(planids[0].action_date.strftime("%d-%B-%Y"))
        capacities = planids.mapped('capacity')
        capacities = list(set(capacities))
        
        column_style = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        _column_style = workbook.add_format({'text_wrap':True, 'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        
        _row_style = workbook.add_format({'font_size': 9, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'vcenter'})
        __row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'align': 'center', 'valign': 'vcenter'})
        
        
        merge_format = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': True, 'align': 'center'})
        
        mc_name = 'QC Balance'
        sheet = workbook.add_worksheet(mc_name[:41])
        sheet.set_column(0, 0, 20)
        sheet.set_column(2, 2, 20)
        sheet.set_column(6, 6, 20)
        # sheet.set_column(5, 5, 15)
        # sheet.set_column(7, 7, 15)
        # sheet.set_column(9, 9, 15)
        # sheet.merge_range(0, 0, 0, 9, 'Painting Plan', merge_format)
        
        sheet.write(2, 0, "OA", column_style)
        sheet.write(2, 1, "PLAN DATE", column_style)
        sheet.write(2, 2, "SHADE", column_style)
        sheet.write(2, 3, "QTY", column_style)
        sheet.write(2, 4, "QC PASS", column_style)
        sheet.write(2, 5, "TAPE SHORT", column_style)
        sheet.write(2, 6, "Remarks", column_style)
        report_data = []
        for pid in planids:
            slider = pid.slidercodesfg.split("TZP-",1)[1]
            order_data = [
                pid.action_date.strftime("%m-%d"),
                int(pid.oa_id.name.replace('OA','0')),
                slider,
                pid.shade,
                pid.finish,
                pid.qty,
                '',
                '',
                '',
                ''
                ]
            report_data.append(order_data)
        row = 3        
        for line in report_data:
            col = 0
            for l in line:
                sheet.write(row, col, l, _row_style)
                # if col == 6:
                #     sheet.write(row, col, l, __row_style)
                # else:
                #     sheet.write(row, col, l, _row_style)
                    
                col += 1
            row += 1


