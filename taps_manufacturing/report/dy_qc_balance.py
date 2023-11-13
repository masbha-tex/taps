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
    
    def generate_xlsx_report(self, workbook, data, qcids):
        plan_date = 'Date: '+ str(qcids[0].action_date.strftime("%d-%B-%Y"))
        capacities = qcids.mapped('capacity')
        capacities = list(set(capacities))
        
        column_style = workbook.add_format({'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        _column_style = workbook.add_format({'text_wrap':True, 'bold': True, 'font_size': 9, 'align': 'center', 'valign': 'vcenter'})
        
        _row_style = workbook.add_format({'font_size': 9, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'vcenter'})
        __row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'align': 'center', 'valign': 'vcenter'})
        
        
        merge_format = workbook.add_format({'font_size': 10, 'align': 'top', 'bold': True, 'align': 'center'})

        items = qcids.mapped('fg_categ_type')
        items = list(set(items))
        
        for item in items:
            mc_name = item
            # mc_name = 'QC Balance'
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
    
            planids = qcids.filtered(lambda pr: pr.fg_categ_type == item)
            all_plans = planids.mapped('parent_id.plan_id')
            # plandates = planids.mapped('action_date')
            for pid in all_plans:
                plan_records = planids.filtered(lambda pr: pr.parent_id.plan_id == pid)
                shades = plan_records.mapped('shade')
                for sh in shades:
                    sh_records = plan_records.filtered(lambda pr: pr.shade == sh)
                    # oa_ids = sh_records.mapped('oa_id')
                    oa_ = sh_records.mapped('oa_id.name')
                    oa_names = [str(int(record.replace('OA','0'))) for record in oa_]
                    oa_names_str = '+'.join(oa_names)
                    bl_qty = sum(sh_records.mapped('balance_qty'))
                    
                # for pid in planids:
                    # slider = pid.slidercodesfg.split("TZP-",1)[1]
                    order_data = [
                        oa_names_str,
                        plan_records[0].action_date.strftime("%d/%m"),
                        sh,
                        bl_qty,
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


