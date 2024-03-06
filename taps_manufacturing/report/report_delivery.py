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
        title_text = del_ids[0].company_id.partner_id.street
        title_text = "\n".join([title_text,'CARTON WISE PACKING DETAILS'])
        title_text = "\n".join([title_text,'DELIVERY DATE : '+ str(del_ids[0].action_date.strftime("%d-%m-%Y"))])
        exporter = del_ids[0].company_id.partner_id.street
        exporter = "\n".join([exporter,del_ids[0].company_id.partner_id.street2+ del_ids[0].company_id.partner_id.city+' '+ del_ids[0].company_id.partner_id.zip])
        exporter = "\n".join([exporter,del_ids[0].company_id.partner_id.country_id.name])

        # buyer = 'BUYER: '+del_ids[0].buyer_name
        buyer = "'BUYER: '+del_ids[0].buyer_name"
        customer = 'CUSTOMER: '+del_ids[0].partner_id.name
        style_ref = 'STYLE REF: ' + (del_ids[0].oa_id.style_ref or '')
        invoice_no = 'INVOICE NO: ' + (del_ids[0].mrp_delivery.name or '')
        oa_no = 'OA NO: '+del_ids[0].oa_id.name
        po_no = 'PO NO: '+(del_ids[0].oa_id.po_no or '')
        pi_no = 'PI NO: '+ (del_ids[0].oa_id.pi_number or '')
        item_name = del_ids[0].fg_categ_type + del_ids[0].finish + del_ids[0].slidercodesfg
        del_ids = del_ids.sorted(key = 'name')
        carton = del_ids.mapped('name')
        carton = list(set(carton))
        report_name = 'Carton Label'#orders.name
        # for m in machines:
        #     raise UserError((m.name))

        sheet = workbook.add_worksheet(report_name[:41])
        column_style = workbook.add_format({'bold': True, 'font_size': 11, 'text_wrap':True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'middle'})
        
        _row_style = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        _row_style_m = workbook.add_format({'font_size': 11, 'font':'Arial', 'left': True,'right': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top', 'bold': True, 'align': 'center', 'text_wrap':True, 'left': True, 'top': True, 'right': True, 'bottom': True})
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


        row = 5
        
        order_data = []
        report_data = []
        for c in carton:
            cr_no = c
            cartoon_details = del_ids.filtered(lambda pr: pr.name == c).sorted(key=lambda pr: pr.shade)
            shade = cartoon_details.mapped('shade')
            shade = list(set(shade))
            cr_pcs = sum(cartoon_details.mapped('qty'))
            for sh in shade:
                lines = sh.splitlines()
                shade_ = lines[0]
                # raise UserError((lines[0]))
                shade_details = cartoon_details.filtered(lambda pr: pr.shade == sh).sorted(key=lambda pr: pr.sizein and pr.sizecm)
                size = None
                size = shade_details.mapped('sizein')
                if 'N/A' in size:
                    size = shade_details.mapped('sizecm')
                size = list(set(size))
                for si in size:
                    size_ = si
                    size_details = shade_details.filtered(lambda pr: pr.sizein == si or pr.sizecm == si)
                    full_pack = 0
                    qty_pack = 0
                    partial_p = []
                    for sq in size_details:
                        if sq.fr_pcs_pack>0:
                            full_pack += sq.pack_qty - 1
                            qty_pack += sq.qty - sq.fr_pcs_pack
                            partial_p.append([(sq.fr_pcs_pack)])
                        else:
                            full_pack += sq.pack_qty
                            qty_pack += sq.qty
                    if full_pack>0:
                        order_data = []
                        order_data = [cr_no,shade_,size_,
                            size_details[0].product_template_id.pack_qty,full_pack,qty_pack,cr_pcs,0,0]
                        report_data.append(order_data)
                        cr_no = ''
                        shade_ = ''
                        size_ = ''
                    if partial_p:
                        for p in partial_p:
                            order_data = []
                            order_data = [cr_no,shade_,si,int(p[0]),1,int(p[0]),cr_pcs,0,0]
                            report_data.append(order_data)
                            cr_no = ''
                            shade_ = ''
                            size_ = ''

            
        row += 1
        for line in report_data:
            col = 0
            for l in line:
                if col == 0 and l == '':
                    sheet.write(row, col, l, _row_style_m)
                else:
                    sheet.write(row, col, l, _row_style)
                col += 1
            row += 1
            # if row == 8:
            #     break

        row += 1
        sheet.merge_range(row, 0, row, 8, 'DELIVERY SUMMARY',merge_format)
        row += 1
        sheet.merge_range(row, 0, row, 1, 'SHADE',merge_format)
        sheet.write(row, 2,  'Size', column_style)
        sheet.write(row, 3,  'OA QTY', column_style)
        sheet.write(row, 4,  '1ST DEL', column_style)
        sheet.write(row, 5,  '2ND DEL', column_style)
        sheet.write(row, 6,  '3RD DEL', column_style)
        sheet.write(row, 7,  '4th DEL', column_style)
        sheet.write(row, 8,  '5th DEL', column_style)
        sheet.write(row, 9,  '6th DEL', column_style)
        sheet.write(row, 10,  '7th DEL', column_style)
        sheet.write(row, 11, 'SAMPLE', column_style)
        sheet.write(row, 12,  'BALANCE', column_style)
        
        # mr = self.env["operation.details"].search([('oa_id','=',del_ids[0].oa_id.id),
        #                                            ('next_operation','=','Operation Packing')]).sorted(key=lambda pr: pr.shade)
        mr = self.env["operation.packing"].search([('oa_id','=',del_ids[0].oa_id.id)]).sorted(key=lambda pr: pr.shade)
        # raise UserError((del_ids[0].oa_id.id))
        # if mr:
            # raise UserError((del_ids[0].oa_id.id))
        shades = mr.mapped('shade')
        report_data = []
        shades = list(set(shades))
        # raise UserError((shades))
        for shad in shades:
            all_size = mr.search([('shade','=',shade)])#filtered(lambda pr: pr.shade == shade)
            sizes = all_size.mapped('sizcommon')
            sizes = list(set(sizes))
            # raise UserError((sizes))
            for size in sizes:
                single_size = all_size.filtered(lambda pr: pr.sizcommon == size)
                qty = sum(single_size.mapped('actual_qty'))
                delivered = self.env["operation.details"].search([('oa_id','=',del_ids[0].oa_id.id),('next_operation','=','Delivery'),('shade','=',shad),('sizcommon','=',size)])
                total_del = sum(delivered.mapped('qty'))
                unique_dates = set(record.action_date.date() for record in delivered)
                num_unique_dates  = len(unique_dates)
                # raise UserError((num_unique_dates))
                fst_del = snd_del = trd_del = frt_del = fit_del = sit_del = set_del = 0
                in_num = 0
                for dt in range(num_unique_dates):
                    datewise = delivered.filtered(lambda pr: pr.action_date.date() == dt)
                    d_qty = sum(delivered.mapped('qty'))
                    if in_num == 0:
                        fst_del = d_qty
                    if in_num == 1:
                        snd_del = d_qty
                    if in_num == 2:
                        trd_del = d_qty
                    if in_num == 3:
                        frt_del = d_qty
                    if in_num == 4:
                        fit_del = d_qty
                    if in_num == 5:
                        sit_del = d_qty
                    if in_num == 6:
                        set_del = d_qty
                    in_num += 1

                r_data = []
                r_data = [shad,size,qty,fst_del,snd_del,trd_del,frt_del,fit_del,sit_del,set_del,0,total_del]
                report_data.append(r_data)
    

        # raise UserError((fst_del,snd_del,trd_del,frt_del,fit_del,sit_del,set_del))
        row += 1
        for re in report_data:
            sheet.merge_range(row, 0, row, 1, re[0], _row_style)    
            sheet.write(row, 2, re[1], _row_style)
            sheet.write(row, 3, re[2], _row_style)
            sheet.write(row, 4, re[3], _row_style)
            sheet.write(row, 5, re[4], _row_style)
            sheet.write(row, 6, re[5], _row_style)
            sheet.write(row, 7, re[6], _row_style)
            sheet.write(row, 8, re[7], _row_style)
            sheet.write(row, 9, re[8], _row_style)
            sheet.write(row, 10, re[9], _row_style)
            sheet.write(row, 11, re[10], _row_style)
            sheet.write(row, 12, re[11], _row_style)
            row += 1
            
        # if mr:
        #     for m in mr:
        #         row += 1
        #         delivered = self.env["operation.details"].search([('oa_id','=',del_ids[0].oa_id.id),('next_operation','=','Delivery'),('mrp_line','=',m.id)])
                # total_del = 0
                # del_dates = None
                # unique_dates = None
                # fst_del = snd_del = trd_del = 0
                # if delivered:
                #     total_del = sum(delivered.mapped('qty'))
                #     unique_dates = set(record.action_date.date() for record in delivered)
                #     # del_dates = delivered.mapped('action_date')
                # if unique_dates:
                #     num_unique_dates  = len(unique_dates)
                #     raise UserError((num_unique_dates))
                #     for dt in range(num_unique_dates):
                #         if dt == 0:
                #             fst_del = 0
                #         if dt == 1:
                #             snd_del = 0
                #         if dt >= 3:
                #             trd_del = 0
                            
                    # raise UserError((unique_dates[0]))
                # sheet.merge_range(row, 0, row, 1, m.shade, _row_style)    
                # sheet.write(row, 1, m.shade, _row_style)
                # sheet.write(row, 2, m.sizecm, _row_style)
                # sheet.write(row, 3, m.product_uom_qty, _row_style)
                # sheet.write(row, 4, fst_del, _row_style)
                # sheet.write(row, 5, snd_del, _row_style)
                # sheet.write(row, 6, trd_del, _row_style)
                # sheet.write(row, 7, 0, _row_style)
                # sheet.write(row, 8, m.product_uom_qty - total_del, _row_style)
            

        
