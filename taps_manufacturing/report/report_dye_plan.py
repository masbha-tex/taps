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
        # raise UserError (planids.default_search_id)
        # self.env['operation.details'].search([('id','in',planids)])
        operations = self.env['operation.details'].search([('id','in',planids.ids)])
        mc_name = str(planids[0].capacity) + 'kgs MC Plan'
        plan_date = 'Date: '+ str(planids[0].action_date.strftime("%d-%m-%Y"))

        
        # raise UserError((mc_name,plan_date))
        
        machines = planids.mapped('machine_no')
        report_name = 'Machine Wise Plan'#orders.name
        # for m in machines:
        #     raise UserError((m.name))

        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

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


        # operations = self.env['operation.details'].search([('id','in',planids.ids)])
        
        # machines = planids.mapped('machine_no')
        # report_name = 'Machine Wise Plan'#orders.name
        row = 2
        for m in machines:
            m_plan = operations.filtered(lambda pr: pr.machine_no.id == m.id)
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
                    sheet.write(row, col, l, format_label_4)
                    col += 1
                row += 1
                

            
        # _range = 1
        # row = 3
        # for orders in planids:
        #         sizein = o_data.sizein
        #         sizecm = o_data.sizecm
        #         if sizein == 'N/A':
        #             sizein = ''
        #         if sizecm == 'N/A':
        #             sizecm = ''
                
        #         m_order = self.env['manufacturing.order'].search([('sale_order_line','=',o_data.id)])
        #         ready_qty = sum(m_order.mapped('done_qty'))
        #         # raise UserError((o_data.id,ready_qty))
        #         balance_qty = o_data.product_uom_qty-ready_qty
        #         order_data = [
        #             customer,
        #             pr_name,
        #             slider,
        #             finish,
        #             pi_num,
        #             oa_num,
        #             create_date,
        #             '',
        #             remarks,
        #             #expected_date,
        #             shade,
        #             sizein,
        #             sizecm,
        #             o_data.product_uom_qty,
        #             ready_qty,
        #             balance_qty,
        #             o_data.tape_con,
        #             shadewise_tape,
        #             o_data.wire_con,
        #             o_data.slider_con,
        #             o_data.botomwire_con,
        #             o_data.topwire_con,
        #             #o_data.pinbox_con,
        #             orders.sale_representative.name,
        #         ]
        #         report_data.append(order_data)
        #     if _range > 0:
        #         _range += 1
        #     _range += len(report_data)
        #     sheet.set_column(0, 0, 20)
        #     sheet.set_column(1, 1, 30)
        #     sheet.set_column(2, 2, 20)
        #     sheet.set_column(3, 3, 20)
        #     sheet.set_column(4, 4, 20)
        #     sheet.set_column(5, 5, 20)
        #     sheet.set_column(8, 8, 40)
        #     sheet.set_column(9, 9, 40)
        #     sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
        #     #sheet.merge_range(1, 1, _range, 1, '', merge_format)
        #     #sheet.merge_range(1, 2, _range, 2, '', merge_format)
        #     #sheet.merge_range(1, 3, _range, 3, '', merge_format)
        #     sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
        #     sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
        #     sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
        #     sheet.merge_range(row_rang, 7, _range, 7, '', merge_format)
        #     sheet.merge_range(row_rang, 8, _range, 8, '', merge_format)
            
        #     qty_total = 0
        #     shade_total = 0
        #     wire_total = 0
        #     slider_total = 0
        #     bottom_total = 0
        #     top_total = 0
            
            
        #     col = 0
        #     row = row_rang
        #     inline_row = 1
        #     row_p = 0
        #     row_sl = 0
        #     row_f = 0
        #     row_sh = 0
            
        #     product_range += product_range
        #     slider_range += slider_range
        #     finish_range += finish_range
        #     shade_range += shade_range
            
        #     for line in report_data:
                    
        #         for x in report_data[row_p:]:
        #             p_last_one = row
        #             if (x[1] == line[1]):
        #                 product_range += 1
        #                 row_p += 1
        #             else:
        #                 sheet.merge_range(row, 1, product_range, 1, '', merge_format)
        #                 product_range = row
        #                 break
        #             if _range == product_range:
        #                 sheet.merge_range(p_last_one, 1, product_range, 1, '', merge_format)
        #                 product_range = row
        #         for x in report_data[row_sl:]:
        #             sl_last_one = row
        #             if (x[2] == line[2]):
        #                 slider_range += 1
        #                 row_sl += 1
        #             else:
        #                 sheet.merge_range(row, 2, slider_range, 2, '', merge_format)
        #                 slider_range = row
        #                 break
        #             if _range == slider_range:
        #                 sheet.merge_range(sl_last_one, 2, slider_range, 2, '', merge_format)
        #                 slider_range = row
        #         for x in report_data[row_f:]:
        #             f_last_one = row
        #             if (x[3] == line[3]):
        #                 finish_range += 1
        #                 row_f += 1
        #             else:
        #                 sheet.merge_range(row, 3, finish_range, 3, '', merge_format)
        #                 finish_range = row
        #                 break
        #             if _range == finish_range:
        #                 sheet.merge_range(f_last_one, 3, finish_range, 3, '', merge_format)
        #                 finish_range = row
    
        #         for x in report_data[row_sh:]:
        #             last_one = row
        #             if (x[9] == line[9]):
        #                 shade_range += 1
        #                 row_sh += 1
        #             else:
        #                 sheet.merge_range(row, 9, shade_range, 9, '', merge_format)
        #                 sheet.merge_range(row, 16, shade_range, 16, '', merge_format_)
        #                 shade_range = row
        #                 break
        #             if _range == shade_range:
        #                 sheet.merge_range(last_one, 9, shade_range, 9, '', merge_format)
        #                 sheet.merge_range(last_one, 16, shade_range, 16, '', merge_format_)
        #                 shade_range = row
                        
        #         col = 0
        #         for l in line:
        #             if col in(0,6,7):
        #                 sheet.write(row, col, l, format_label_1)
        #             elif col in(1,2,3):
        #                 sheet.write(row, col, l, format_label_2)
        #             elif col in(4,5):
        #                 sheet.write(row, col, l, format_label_3)
        #             elif col in(8,9):
        #                 sheet.write(row, col, l, format_label_4)
        #             elif col == 14:
        #                 sheet.write(row, col, '=M{1}-N{1}'.format(row+1, row+1), row_style)
        #             else:
        #                 sheet.write(row, col, l, row_style)
        #             if col == 12:
        #                 qty_total += l
        #             if col == 15:
        #                 shade_total += l
        #             if col == 17:
        #                 wire_total += l
        #             if col == 18:
        #                 slider_total += l
        #             if col == 19:
        #                 bottom_total += l
        #             if col == 20:
        #                 top_total += l
        #             col += 1
                    
        #         row += 1
        #         inline_row += 1
        #         row_p = row_sl = row_f = row_sh = inline_row-1
            
        #     sheet.write(row, 0, '')
        #     sheet.write(row, 1, '')
        #     sheet.write(row, 2, '')
        #     sheet.write(row, 3, '')
        #     sheet.write(row, 4, '')
        #     sheet.write(row, 5, '')
        #     sheet.write(row, 6, '')
        #     sheet.write(row, 7, '')
        #     sheet.write(row, 8, '')
        #     sheet.write(row, 9, '')
        #     sheet.write(row, 10, '')
        #     sheet.write(row, 11, '')
        #     sheet.write(row, 12, '=SUM(M{0}:M{1})'.format(row_rang+1, row), row_style)
        #     sheet.write(row, 13, '=SUM(N{0}:N{1})'.format(row_rang+1, row), row_style)
        #     sheet.write(row, 14, '=M{1}-N{1}'.format(row+1, row+1), row_style)
        #     sheet.write(row, 15, '')
        #     sheet.write(row, 16, shade_total, row_style)
        #     sheet.write(row, 17, wire_total, row_style)
        #     sheet.write(row, 18, slider_total, row_style)
        #     sheet.write(row, 19, bottom_total, row_style)
        #     sheet.write(row, 20, top_total, row_style)
        #     sheet.write(row, 21, '')


