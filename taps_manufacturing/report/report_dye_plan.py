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
        plan_date = 'Date: '+ str(planids[0].action_date.strftime("%d-%B-%Y"))
        capacities = planids.mapped('capacity')
        capacities = list(set(capacities))
        
        column_style = workbook.add_format({'bold': True, 'font_size': 11, 'align': 'center', 'valign': 'vcenter'})
        
        _row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'vcenter'})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top', 'bold': True, 'align': 'center'})
        merge_format_ = workbook.add_format({'align': 'bottom', 'bold': True})
        
        for m_capa in capacities:
            fl_planids = planids.filtered(lambda pr: pr.capacity == m_capa)
            mc_name = str(fl_planids[0].machine_no.display_capacity) +'kgs MC Plan'
            
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
                plan_ids = m_plan.mapped('plan_id')
                plan_ids = list(set(plan_ids))

                for pid in plan_ids: 
                    single_plan = m_plan.filtered(lambda pr: pr.plan_id == pid)
                    plq = sum(single_plan.mapped('qty'))
                    dnq = sum(single_plan.mapped('done_qty'))
                    plan_lots = math.ceil(plq/m_capa)
                    oa_ = single_plan.mapped('oa_id.name')
                    oa_names = [str(int(record.replace('OA','0'))) for record in oa_]
                    oa_names_str = ','.join(oa_names)
                    
                    rest_plq = plq/plan_lots
                    rest_dnq = dnq
                    all_lots = plan_lots
                        
                    for lot in range(all_lots):
                        qty = rest_plq
                        order_data = []
                        shade_ref = ''
                        remarks = ''
                        if single_plan[0].shade_ref:
                            shade_ref = single_plan[0].shade_ref
                        if single_plan[0].plan_remarks:
                            remarks = single_plan[0].plan_remarks
                        action_date = single_plan[0].action_date.strftime("%d-%B-%Y")
                        oa_date = single_plan[0].date_order.strftime("%d-%B-%Y")
                        # print(txt[txt.index("l"):txt.find("c")])
                        f_part = single_plan[0].fg_categ_type[0:1]
                        invisible_ = single_plan[0].product_template_id.name.find('INVISIBLE')
                        if invisible_>0:
                            f_part = 'I'
                        item = f_part + single_plan[0].fg_categ_type[single_plan[0].fg_categ_type.index("#"):single_plan[0].fg_categ_type.index("#")+2]
                        order_data = [
                            oa_names_str,
                            action_date,
                            oa_date,
                            single_plan[0].partner_id.name,
                            single_plan[0].buyer_name,
                            item,
                            single_plan[0].shade,shade_ref,
                            qty,'','','','','','','','',remarks
                            ]
                        report_data.append(order_data)
                        
                if len(report_data) < 7:
                    row_sl = len(report_data)
                    for l in range(row_sl,7):
                        order_data = ['','','','','','','','','','','','','','','','','','']
                        report_data.append(order_data)
                for line in report_data:
                    col = 0
                    for l in line:
                        sheet.write(row, col, l, _row_style)
                        col += 1
                    row += 1


