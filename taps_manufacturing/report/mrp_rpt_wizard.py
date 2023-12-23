import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta
import re
import math
import calendar
_logger = logging.getLogger(__name__)


class MrpReportWizard(models.TransientModel):
    _name = 'mrp.report'
    _description = 'MRP Reports'
    _check_company_auto = True
    
    # is_company = fields.Boolean(readonly=False, default=False)
    
    report_type = fields.Selection([('pir', 'PI File'),('pic', 'Closed PI'),('pis', 'PI Summary'),('dpr', 'Invoice'),('dppr', 'Packing Production Report'),('dpcl', 'Production Report (FG)')], string='Report Type', required=True, help='Report Type', default='pir')
    
    date_from = fields.Date('Date from', readonly=False)
    date_to = fields.Date('Date to', readonly=False)
    
    month_list = fields.Selection('_get_month_list', 'Month') #, default=lambda self: self._get_month_list()

    file_data = fields.Binary(readonly=True, attachment=False)
    

    @staticmethod
    def _get_year_list():
        current_year = datetime.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 1):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((next_year, year_label))
        return year_options 
    
    @staticmethod
    def _get_month_list():
        month_list = []
        for month in range(12):
            mon = month + 1
            month_label = f'{datetime.today().replace(day=1).replace(month=mon).strftime("%B-%Y")}'
            #{year_str}-{next_year[2:]}
            month_list.append((mon, month_label))
        return month_list     

    @staticmethod
    def _get_default_year():
        current_year = datetime.today().year
        return str(current_year+1)  

    
    def action_generate_xlsx_report(self):
        if self.report_type == "pir":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            return self.pi_xls_template(self, data=data)
        if self.report_type == "pis":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            return self.pis_xls_template(self, data=data)
        if self.report_type == "dpr":
            data = {'month_list': self.month_list}
            return self.daily_pr_xls_template(self, data=data)
        if self.report_type == "dpcl":
            data = {'month_list': self.month_list}
            return self.daily_closed_xls_template(self, data=data)
        if self.report_type in ("dppr", "pic"):
            if self.date_from == False or self.date_to == False:
                raise UserError(('Select From and To date'))
            elif self.date_from > self.date_to:
                raise UserError(('From date must be less then To date'))
            else:
                data = {'date_from': self.date_from,'date_to': self.date_to}
                if self.report_type == "pic":
                    return self.closed_pi_xls_template(self, data=data)
                return self.packing_xls_template(self, data=data)

    def pi_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        # domain = []
        # if data.get('date_from'):
        #     domain.append(('date_from', '=', data.get('date_from'))) 
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel'))])
        if data.get('date_from'):
            if data.get('date_to'):
                running_orders = running_orders.filtered(lambda pr: pr.date_order.date() >= data.get('date_from') and pr.date_order.date() <= data.get('date_to'))
            else:
                running_orders = running_orders.filtered(lambda pr: pr.date_order.date() == data.get('date_from'))
                
        # running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None)])
        m_orders = running_orders.search([('revision_no','=',None)])
        
        rev_orders = running_orders - m_orders
        
        m_orders = running_orders
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})
        

        fg_items = m_orders.mapped('fg_categ_type')
        fg_items = list(set(fg_items))
        items = self.env['fg.category'].search([('active','=',True)]).sorted(key=lambda pr: pr.sequence)
        
        if rev_orders:
            fg_items.append('Revised PI')
        else:
            items = items.filtered(lambda pr: pr.name != 'Revised PI').sorted(key=lambda pr: pr.sequence)
        
        de_items = items.filtered(lambda pr: pr.name not in (fg_items))
        exists_items = items - de_items
        items = exists_items.sorted(key=lambda pr: pr.sequence)

        for item in items:
            all_orders = None
            if item.name == 'Revised PI':
                all_orders = self.env['sale.order.line'].browse(rev_orders.sale_order_line.ids)
            else:
                all_orders = self.env['sale.order.line'].browse(m_orders.sale_order_line.ids)
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type == item.name)
            
            sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = item.name
            # raise UserError((items))
           
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            
            sheet.freeze_panes(1, 0)
            
            sheet.write(0, 0, "CUSTOMER NAME", column_style)
            sheet.write(0, 1, "PRODUCT", column_style)
            sheet.write(0, 2, "SLIDER CODE", column_style)
            sheet.write(0, 3, "FINISH", column_style)
            sheet.write(0, 4, "PI NO", column_style)
            sheet.write(0, 5, "OA NO", column_style)
            sheet.write(0, 6, "OA DATE", column_style)
            sheet.write(0, 7, "Production DATE", column_style)
            sheet.write(0, 8, "DETAILS", column_style)
            #sheet.write(1, 9, "DELIVERY DATE", column_style)
            sheet.write(0, 9, "SHADE", column_style)
            sheet.write(0, 10, "SIZE(INCH)", column_style)
            sheet.write(0, 11, "SIZE(CM)", column_style)
            sheet.write(0, 12, "ORDER QTY", column_style)
            sheet.write(0, 13, "READY QTY", column_style)
            sheet.write(0, 14, "PENDING QTY", column_style)
            sheet.write(0, 15, "TOTAL WT/KG", column_style)
            sheet.write(0, 16, "SHADE TOTAL", column_style)
            sheet.write(0, 17, "WIRE/KG", column_style)
            sheet.write(0, 18, "SLIDER/PCS", column_style)
            sheet.write(0, 19, "H-BOTTOM/KG", column_style)
            sheet.write(0, 20, "U-TOP/KG", column_style)
            #sheet.write(0, 18, "PINBOX/KG", column_style)
            sheet.write(0, 21, "SALESPERSON", column_style)

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(8, 8, 40)
            sheet.set_column(9, 9, 40)

            
            row_rang = 1
            _range = 0
            
            row_p = 0
            row_sl = 0
            row_f = 0
            row_sh = 0
            
            product_range = 0
            slider_range = 0
            finish_range = 0
            shade_range = 0
            
            for orders in sale_orders:
                docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
                
                report_data = []
                order_data = []
                # slnumber=0
                customer = ''
                pi_num = ''
                oa_num = ''
                remarks = ''
                create_date = ''
                expected_date = ''
                for x,o_data in enumerate(docs):
                    # slnumber = slnumber+1 orders.buyer_name.name,
                    if x == 0:
                        customer = "\n".join([orders.partner_id.name,"\n",orders.payment_term_id.name])
                        pi_num = orders.order_ref.pi_number
                        oa_num = orders.name
                        remarks = orders.remarks
                        create_date = orders.create_date.strftime("%d-%m-%Y")
                        expected_date = ''#orders.expected_date.strftime("%d-%m-%Y")
                    else:
                        customer = ''
                        pi_num = ''
                        oa_num = ''
                        remarks = ''
                        create_date = ''
                        expected_date = ''
                    
                    pr_name = o_data.product_template_id.name
                    if o_data.numberoftop:
                        pr_name = "\n".join([pr_name,o_data.numberoftop])
                    if o_data.ptopfinish:
                        pr_name = "\n".join([pr_name,o_data.ptopfinish])
                    if o_data.pbotomfinish:
                        pr_name = "\n".join([pr_name,o_data.pbotomfinish])
                    if o_data.ppinboxfinish:
                        pr_name = "\n".join([pr_name,o_data.ppinboxfinish])
                    if o_data.topbottom:
                        pr_name = "\n".join([pr_name,o_data.topbottom])
                    slider = o_data.slidercodesfg
                    finish = o_data.finish #.replace('\n',' ')
                    shade = o_data.shade
                    shadewise_tape = o_data.shadewise_tape
                    
                    sizein = o_data.sizein
                    sizecm = o_data.sizecm
                    if sizein == 'N/A':
                        sizein = ''
                    if sizecm == 'N/A':
                        sizecm = ''
                    
                    m_order = self.env['manufacturing.order'].search([('sale_order_line','=',o_data.id)])
                    ready_qty = sum(m_order.mapped('done_qty'))
                    # raise UserError((o_data.id,ready_qty))
                    balance_qty = o_data.product_uom_qty - ready_qty
                    order_data = [
                        customer,
                        pr_name,
                        slider,
                        finish,
                        pi_num,
                        oa_num,
                        create_date,
                        '',
                        remarks,
                        #expected_date,
                        shade,
                        sizein,
                        sizecm,
                        o_data.product_uom_qty,
                        ready_qty,
                        balance_qty,
                        o_data.tape_con,
                        shadewise_tape,
                        o_data.wire_con,
                        o_data.slider_con,
                        o_data.botomwire_con,
                        o_data.topwire_con,
                        #o_data.pinbox_con,
                        orders.sale_representative.name,
                    ]
                    report_data.append(order_data)
                if _range > 0:
                    _range += 2
                _range += len(report_data)
                
                sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
                sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
                sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
                sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
                sheet.merge_range(row_rang, 7, _range, 7, '', merge_format)
                sheet.merge_range(row_rang, 8, _range, 8, '', merge_format)
                
                qty_total = 0
                shade_total = 0
                wire_total = 0
                slider_total = 0
                bottom_total = 0
                top_total = 0
                
                
                col = 0
                row = row_rang
                inline_row = 1
                row_p = 0
                row_sl = 0
                row_f = 0
                row_sh = 0
                
                # product_range += product_range
                # slider_range += slider_range
                # finish_range += finish_range
                # shade_range += shade_range
                
                for line in report_data:
                    for x in report_data[row_p:]:
                        p_last_one = row
                        if (x[1] == line[1]):
                            product_range += 1
                            row_p += 1
                        else:
                            sheet.merge_range(row, 1, product_range, 1, '', merge_format)
                            product_range = row
                            break
                        if _range == product_range:
                            sheet.merge_range(p_last_one, 1, product_range, 1, '', merge_format)
                            product_range = row
                    for x in report_data[row_sl:]:
                        sl_last_one = row
                        if (x[2] == line[2]):
                            slider_range += 1
                            row_sl += 1
                        else:
                            sheet.merge_range(row, 2, slider_range, 2, '', merge_format)
                            slider_range = row
                            break
                        if _range == slider_range:
                            sheet.merge_range(sl_last_one, 2, slider_range, 2, '', merge_format)
                            slider_range = row
                    for x in report_data[row_f:]:
                        f_last_one = row
                        if (x[3] == line[3]):
                            finish_range += 1
                            row_f += 1
                        else:
                            sheet.merge_range(row, 3, finish_range, 3, '', merge_format)
                            finish_range = row
                            break
                        if _range == finish_range:
                            sheet.merge_range(f_last_one, 3, finish_range, 3, '', merge_format)
                            finish_range = row
        
                    for x in report_data[row_sh:]:
                        last_one = row
                        if (x[9] == line[9]):
                            shade_range += 1
                            row_sh += 1
                        else:
                            sheet.merge_range(row, 9, shade_range, 9, '', merge_format)
                            sheet.merge_range(row, 16, shade_range, 16, '', merge_format_)
                            shade_range = row
                            break
                        if _range == shade_range:
                            sheet.merge_range(last_one, 9, shade_range, 9, '', merge_format)
                            sheet.merge_range(last_one, 16, shade_range, 16, '', merge_format_)
                            shade_range = row
                            
                    col = 0
                    for l in line:
                        if col in(0,6,7):
                            sheet.write(row, col, l, format_label_1)
                        elif col in(1,2,3):
                            sheet.write(row, col, l, format_label_2)
                        elif col in(4,5):
                            sheet.write(row, col, l, format_label_3)
                        elif col in(8,9):
                            sheet.write(row, col, l, format_label_4)
                        elif col == 14:
                            sheet.write(row, col, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                        else:
                            sheet.write(row, col, l, row_style)
                        if col == 12:
                            qty_total += l
                        if col == 15:
                            shade_total += l
                        if col == 17:
                            wire_total += l
                        if col == 18:
                            slider_total += l
                        if col == 19:
                            bottom_total += l
                        if col == 20:
                            top_total += l
                        col += 1
                        
                    row += 1
                    inline_row += 1
                    row_p = row_sl = row_f = row_sh = inline_row - 1
                
                sheet.write(row, 0, '')
                sheet.write(row, 1, '')
                sheet.write(row, 2, '')
                sheet.write(row, 3, '')
                sheet.write(row, 4, '')
                sheet.write(row, 5, '')
                sheet.write(row, 6, '')
                sheet.write(row, 7, '')
                sheet.write(row, 8, '')
                sheet.write(row, 9, '')
                sheet.write(row, 10, '')
                sheet.write(row, 11, '')
                sheet.write(row, 12, '=SUM(M{0}:M{1})'.format(row_rang+1, row), row_style)
                sheet.write(row, 13, '=SUM(N{0}:N{1})'.format(row_rang+1, row), row_style)
                sheet.write(row, 14, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                sheet.write(row, 15, '')
                sheet.write(row, 16, shade_total, row_style)
                sheet.write(row, 17, wire_total, row_style)
                sheet.write(row, 18, slider_total, row_style)
                sheet.write(row, 19, bottom_total, row_style)
                sheet.write(row, 20, top_total, row_style)
                sheet.write(row, 21, '')

                # row += 1
                row_rang = row + 2
                
                product_range = slider_range = finish_range = shade_range = row_rang - 1
            
            sheet.write(row+1, 0, '')
            sheet.write(row+1, 1, '')
            sheet.write(row+1, 2, '')
            sheet.write(row+1, 3, '')
            sheet.write(row+1, 4, '')
            sheet.write(row+1, 5, '')
            sheet.write(row+1, 6, '')
            sheet.write(row+1, 7, '')
            sheet.write(row+1, 8, '')
            sheet.write(row+1, 9, '')
            sheet.write(row+1, 10, '')
            sheet.write(row+1, 11, '')
            sheet.write(row+1, 12, '=SUM(M{0}:M{1})/2'.format(1, row_rang-1), row_style)
            sheet.write(row+1, 13, '=SUM(N{0}:N{1})/2'.format(1, row_rang-1), row_style)
            sheet.write(row+1, 14, '=M{1}-N{1}'.format(row_rang, row_rang), row_style)
            sheet.write(row+1, 15, '')
            sheet.write(row+1, 16, '')
            sheet.write(row+1, 17, '')
            sheet.write(row+1, 18, '')
            sheet.write(row+1, 19, '')
            sheet.write(row+1, 20, '')
            sheet.write(row+1, 21, '')
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('PI File')),
            'target': 'self',
        }

    def closed_pi_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        closed_orders = self.env['manufacturing.order'].search([('oa_id','!=',None),('state','=','closed'),('closing_date','!=',None)])
        closed_orders = closed_orders.filtered(lambda pr: pr.closing_date.date() >= data.get('date_from') and pr.closing_date.date() <= data.get('date_to'))
                
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

        fg_items = closed_orders.mapped('fg_categ_type')
        fg_items = list(set(fg_items))
        items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
        
        de_items = items.filtered(lambda pr: pr.name not in (fg_items))
        exists_items = items - de_items
        items = exists_items.sorted(key=lambda pr: pr.sequence)

        for item in items:
            all_orders = None
            if item.name == 'Revised PI':
                all_orders = self.env['sale.order.line'].browse(rev_orders.sale_order_line.ids)
            else:
                all_orders = self.env['sale.order.line'].browse(closed_orders.sale_order_line.ids)
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type == item.name)
            
            sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = item.name
            # raise UserError((items))
           
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            
            sheet.freeze_panes(1, 0)
            
            sheet.write(0, 0, "CUSTOMER NAME", column_style)
            sheet.write(0, 1, "PRODUCT", column_style)
            sheet.write(0, 2, "SLIDER CODE", column_style)
            sheet.write(0, 3, "FINISH", column_style)
            sheet.write(0, 4, "PI NO", column_style)
            sheet.write(0, 5, "OA NO", column_style)
            sheet.write(0, 6, "OA DATE", column_style)
            sheet.write(0, 7, "Production DATE", column_style)
            sheet.write(0, 8, "DETAILS", column_style)
            #sheet.write(1, 9, "DELIVERY DATE", column_style)
            sheet.write(0, 9, "SHADE", column_style)
            sheet.write(0, 10, "SIZE(INCH)", column_style)
            sheet.write(0, 11, "SIZE(CM)", column_style)
            sheet.write(0, 12, "ORDER QTY", column_style)
            sheet.write(0, 13, "READY QTY", column_style)
            sheet.write(0, 14, "PENDING QTY", column_style)
            sheet.write(0, 15, "TOTAL WT/KG", column_style)
            sheet.write(0, 16, "SHADE TOTAL", column_style)
            sheet.write(0, 17, "WIRE/KG", column_style)
            sheet.write(0, 18, "SLIDER/PCS", column_style)
            sheet.write(0, 19, "H-BOTTOM/KG", column_style)
            sheet.write(0, 20, "U-TOP/KG", column_style)
            sheet.write(0, 21, "SALESPERSON", column_style)

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 30)
            sheet.set_column(2, 2, 20)
            sheet.set_column(3, 3, 20)
            sheet.set_column(4, 4, 20)
            sheet.set_column(5, 5, 20)
            sheet.set_column(8, 8, 40)
            sheet.set_column(9, 9, 40)

            
            row_rang = 1
            _range = 0
            
            row_p = 0
            row_sl = 0
            row_f = 0
            row_sh = 0
            
            product_range = 0
            slider_range = 0
            finish_range = 0
            shade_range = 0
            
            for orders in sale_orders:
                docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
                
                report_data = []
                order_data = []
                # slnumber=0
                customer = ''
                pi_num = ''
                oa_num = ''
                remarks = ''
                create_date = ''
                expected_date = ''
                for x,o_data in enumerate(docs):
                    # slnumber = slnumber+1 orders.buyer_name.name,
                    if x == 0:
                        customer = "\n".join([orders.partner_id.name,"\n",orders.payment_term_id.name])
                        pi_num = orders.order_ref.pi_number
                        oa_num = orders.name
                        remarks = orders.remarks
                        create_date = orders.create_date.strftime("%d-%m-%Y")
                        expected_date = ''#orders.expected_date.strftime("%d-%m-%Y")
                    else:
                        customer = ''
                        pi_num = ''
                        oa_num = ''
                        remarks = ''
                        create_date = ''
                        expected_date = ''
                    
                    pr_name = o_data.product_template_id.name
                    if o_data.numberoftop:
                        pr_name = "\n".join([pr_name,o_data.numberoftop])
                    if o_data.ptopfinish:
                        pr_name = "\n".join([pr_name,o_data.ptopfinish])
                    if o_data.pbotomfinish:
                        pr_name = "\n".join([pr_name,o_data.pbotomfinish])
                    if o_data.ppinboxfinish:
                        pr_name = "\n".join([pr_name,o_data.ppinboxfinish])
                    if o_data.topbottom:
                        pr_name = "\n".join([pr_name,o_data.topbottom])
                    slider = o_data.slidercodesfg
                    finish = o_data.finish #.replace('\n',' ')
                    shade = o_data.shade
                    shadewise_tape = o_data.shadewise_tape
                    
                    sizein = o_data.sizein
                    sizecm = o_data.sizecm
                    if sizein == 'N/A':
                        sizein = ''
                    if sizecm == 'N/A':
                        sizecm = ''
                    
                    m_order = self.env['manufacturing.order'].search([('sale_order_line','=',o_data.id)])
                    ready_qty = sum(m_order.mapped('done_qty'))
                    # raise UserError((o_data.id,ready_qty))
                    balance_qty = o_data.product_uom_qty - ready_qty
                    order_data = [
                        customer,
                        pr_name,
                        slider,
                        finish,
                        pi_num,
                        oa_num,
                        create_date,
                        '',
                        remarks,
                        #expected_date,
                        shade,
                        sizein,
                        sizecm,
                        o_data.product_uom_qty,
                        ready_qty,
                        balance_qty,
                        o_data.tape_con,
                        shadewise_tape,
                        o_data.wire_con,
                        o_data.slider_con,
                        o_data.botomwire_con,
                        o_data.topwire_con,
                        #o_data.pinbox_con,
                        orders.sale_representative.name,
                    ]
                    report_data.append(order_data)
                if _range > 0:
                    _range += 2
                _range += len(report_data)
                
                sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
                sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
                sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
                sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
                sheet.merge_range(row_rang, 7, _range, 7, '', merge_format)
                sheet.merge_range(row_rang, 8, _range, 8, '', merge_format)
                
                qty_total = 0
                shade_total = 0
                wire_total = 0
                slider_total = 0
                bottom_total = 0
                top_total = 0
                
                
                col = 0
                row = row_rang
                inline_row = 1
                row_p = 0
                row_sl = 0
                row_f = 0
                row_sh = 0
                
                # product_range += product_range
                # slider_range += slider_range
                # finish_range += finish_range
                # shade_range += shade_range
                
                for line in report_data:
                    for x in report_data[row_p:]:
                        p_last_one = row
                        if (x[1] == line[1]):
                            product_range += 1
                            row_p += 1
                        else:
                            sheet.merge_range(row, 1, product_range, 1, '', merge_format)
                            product_range = row
                            break
                        if _range == product_range:
                            sheet.merge_range(p_last_one, 1, product_range, 1, '', merge_format)
                            product_range = row
                    for x in report_data[row_sl:]:
                        sl_last_one = row
                        if (x[2] == line[2]):
                            slider_range += 1
                            row_sl += 1
                        else:
                            sheet.merge_range(row, 2, slider_range, 2, '', merge_format)
                            slider_range = row
                            break
                        if _range == slider_range:
                            sheet.merge_range(sl_last_one, 2, slider_range, 2, '', merge_format)
                            slider_range = row
                    for x in report_data[row_f:]:
                        f_last_one = row
                        if (x[3] == line[3]):
                            finish_range += 1
                            row_f += 1
                        else:
                            sheet.merge_range(row, 3, finish_range, 3, '', merge_format)
                            finish_range = row
                            break
                        if _range == finish_range:
                            sheet.merge_range(f_last_one, 3, finish_range, 3, '', merge_format)
                            finish_range = row
        
                    for x in report_data[row_sh:]:
                        last_one = row
                        if (x[9] == line[9]):
                            shade_range += 1
                            row_sh += 1
                        else:
                            sheet.merge_range(row, 9, shade_range, 9, '', merge_format)
                            sheet.merge_range(row, 16, shade_range, 16, '', merge_format_)
                            shade_range = row
                            break
                        if _range == shade_range:
                            sheet.merge_range(last_one, 9, shade_range, 9, '', merge_format)
                            sheet.merge_range(last_one, 16, shade_range, 16, '', merge_format_)
                            shade_range = row
                            
                    col = 0
                    for l in line:
                        if col in(0,6,7):
                            sheet.write(row, col, l, format_label_1)
                        elif col in(1,2,3):
                            sheet.write(row, col, l, format_label_2)
                        elif col in(4,5):
                            sheet.write(row, col, l, format_label_3)
                        elif col in(8,9):
                            sheet.write(row, col, l, format_label_4)
                        elif col == 14:
                            sheet.write(row, col, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                        else:
                            sheet.write(row, col, l, row_style)
                        if col == 12:
                            qty_total += l
                        if col == 15:
                            shade_total += l
                        if col == 17:
                            wire_total += l
                        if col == 18:
                            slider_total += l
                        if col == 19:
                            bottom_total += l
                        if col == 20:
                            top_total += l
                        col += 1
                        
                    row += 1
                    inline_row += 1
                    row_p = row_sl = row_f = row_sh = inline_row - 1
                
                sheet.write(row, 0, '')
                sheet.write(row, 1, '')
                sheet.write(row, 2, '')
                sheet.write(row, 3, '')
                sheet.write(row, 4, '')
                sheet.write(row, 5, '')
                sheet.write(row, 6, '')
                sheet.write(row, 7, '')
                sheet.write(row, 8, '')
                sheet.write(row, 9, '')
                sheet.write(row, 10, '')
                sheet.write(row, 11, '')
                sheet.write(row, 12, '=SUM(M{0}:M{1})'.format(row_rang+1, row), row_style)
                sheet.write(row, 13, '=SUM(N{0}:N{1})'.format(row_rang+1, row), row_style)
                sheet.write(row, 14, '=M{1}-N{1}'.format(row+1, row+1), row_style)
                sheet.write(row, 15, '')
                sheet.write(row, 16, shade_total, row_style)
                sheet.write(row, 17, wire_total, row_style)
                sheet.write(row, 18, slider_total, row_style)
                sheet.write(row, 19, bottom_total, row_style)
                sheet.write(row, 20, top_total, row_style)
                sheet.write(row, 21, '')

                # row += 1
                row_rang = row + 2
                
                product_range = slider_range = finish_range = shade_range = row_rang - 1
            
            sheet.write(row+1, 0, '')
            sheet.write(row+1, 1, '')
            sheet.write(row+1, 2, '')
            sheet.write(row+1, 3, '')
            sheet.write(row+1, 4, '')
            sheet.write(row+1, 5, '')
            sheet.write(row+1, 6, '')
            sheet.write(row+1, 7, '')
            sheet.write(row+1, 8, '')
            sheet.write(row+1, 9, '')
            sheet.write(row+1, 10, '')
            sheet.write(row+1, 11, '')
            sheet.write(row+1, 12, '=SUM(M{0}:M{1})/2'.format(1, row_rang-1), row_style)
            sheet.write(row+1, 13, '=SUM(N{0}:N{1})/2'.format(1, row_rang-1), row_style)
            sheet.write(row+1, 14, '=M{1}-N{1}'.format(row_rang, row_rang), row_style)
            sheet.write(row+1, 15, '')
            sheet.write(row+1, 16, '')
            sheet.write(row+1, 17, '')
            sheet.write(row+1, 18, '')
            sheet.write(row+1, 19, '')
            sheet.write(row+1, 20, '')
            sheet.write(row+1, 21, '')
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Closed PI')),
            'target': 'self',
        }
    
    def pis_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','!=','closed')])
        if data.get('date_from'):
            if data.get('date_to'):
                running_orders = running_orders.filtered(lambda pr: pr.date_order.date() >= data.get('date_from') and pr.date_order.date() <= data.get('date_to'))
            else:
                running_orders = running_orders.filtered(lambda pr: pr.date_order.date() == data.get('date_from'))
                
        m_orders = running_orders.search([('revision_no','=',None)])
        rev_orders = running_orders - m_orders
        m_orders = running_orders
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        

        fg_items = m_orders.mapped('fg_categ_type')
        fg_items = list(set(fg_items))
        items = self.env['fg.category'].search([('active','=',True)]).sorted(key=lambda pr: pr.sequence)
        
        if rev_orders:
            fg_items.append('Revised PI')
        else:
            items = items.filtered(lambda pr: pr.name != 'Revised PI').sorted(key=lambda pr: pr.sequence)
        
        de_items = items.filtered(lambda pr: pr.name not in (fg_items))
        exists_items = items - de_items
        items = exists_items.sorted(key=lambda pr: pr.sequence)

        for item in items:
            all_orders = None
            if item.name == 'Revised PI':
                all_orders = self.env['sale.order.line'].browse(rev_orders.sale_order_line.ids)
            else:
                all_orders = self.env['sale.order.line'].browse(m_orders.sale_order_line.ids)
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type == item.name)
            
            sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = item.name
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.freeze_panes(1, 0)
            
            sheet.write(0, 0, "OA ID", column_style)
            sheet.write(0, 1, "PI NO", column_style)
            sheet.write(0, 2, "OA NO", column_style)
            sheet.write(0, 3, "OA DATE", column_style)
            sheet.write(0, 4, "ORDER QTY", column_style)
            sheet.write(0, 5, "READY QTY", column_style)
            sheet.write(0, 6, "PENDING QTY", column_style)
            # docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
            report_data = []
            for orders in sale_orders:
                # docs = self.env['sale.order.line'].search([('order_id', '=', orders.id)])
                create_date = orders.create_date.strftime("%d-%m-%Y")
                m_order = self.env['manufacturing.order'].search([('oa_id','=',orders.id)])
                ready_qty = sum(m_order.mapped('done_qty'))
                balance_qty = orders.total_product_qty - ready_qty
                order_data = []
                order_data = [
                    orders.id,
                    orders.order_ref.pi_number,
                    orders.name,
                    create_date,
                    orders.total_product_qty,
                    ready_qty,
                    balance_qty,
                ]
                report_data.append(order_data)
            row = 1    
            for line in report_data:
                col = 0
                for l in line:
                    sheet.write(row, col, l, row_style)
                    col += 1
                row += 1
                
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('PI Summary')),
            'target': 'self',
        }
    

    def iterate_days(self, year, month):
        # Get the number of days in the given month
        _, last_day = calendar.monthrange(year, month)
    
        # Iterate over all days in the month
        for day in range(1, last_day + 1):
            yield day

    def daily_pr_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        month_ = None
        if data.get('month_list'):
            month_ = data.get('month_list')
        year = datetime.today().year
        
        all_outputs = self.env['operation.details'].search([('next_operation','=','FG Packing')])
        daily_outputs = all_outputs.filtered(lambda pr: pr.action_date.month == int(month_) and pr.action_date.year == year)#.sorted(key=lambda pr: pr.sequence)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center'})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})#'num_format': '$#,##0'
        
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

        initial_pr = self.env['initial.production'].search([('company_id','=',self.env.company.id)])

        for day in self.iterate_days(year, int(month_)):
            comu_outputs = daily_outputs.filtered(lambda pr: pr.action_date.day <= day)
            datewise_outputs = daily_outputs.filtered(lambda pr: pr.action_date.day == day)
            report_name = day
            
            full_date = fields.datetime.now().replace(day = 1).replace(month = int(month_)).replace(year = year)
            first_day_of_m = full_date # first day of month
            full_date = full_date.replace(day = day)
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.freeze_panes(1, 0)
            if start_time.date() == full_date.date():
                sheet.activate()
                
            sheet.write(0, 0, "PRODUCT", column_style)
            sheet.write(0, 1, "PACKING PCS", column_style)
            sheet.write(0, 2, "INVOICE USD", column_style)
            sheet.write(0, 3, "PENDING PCS", column_style)
            sheet.write(0, 4, "PENDING USD", column_style)
            sheet.write(0, 5, "COMULATIVE PRODUCTION", column_style)
            sheet.write(0, 6, "COMULATIVE INVOICING", column_style)
            sheet.write(0, 7, "TODAY RELEASED", column_style)
            sheet.write(0, 8, "COMULATIVE RELEASED", column_style)
            sheet.write(0, 9, "PENDING OA", column_style)

            sheet.set_column(0, 0, 20)
            sheet.set_column(1, 1, 15)
            sheet.set_column(2, 2, 15)
            sheet.set_column(3, 3, 15)
            sheet.set_column(4, 4, 15)
            sheet.set_column(5, 5, 15)
            sheet.set_column(6, 6, 15)
            sheet.set_column(7, 7, 15)
            sheet.set_column(8, 8, 15)
            sheet.set_column(9, 9, 15)
            
            # items = datewise_outputs.mapped('fg_categ_type')
            # items = list(set(items))
            running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel'))])
            
            items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
            
            report_data = []
            closed_ids = 0
            for item in items:
                comu_outputs = comu_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
                itemwise_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
                comu_pcs = sum(comu_outputs.mapped('qty'))
                pack_pcs = sum(itemwise_outputs.mapped('qty'))
                # invoiced = round(sum(itemwise_outputs.mapped('sale_order_line.price_subtotal')),2)
                #sum(order.qty * order. for order in itemwise_outputs)

                in_pr = initial_pr.filtered(lambda pr: pr.fg_categ_type == item.name)
                
                all_released = self.env['manufacturing.order'].search([('fg_categ_type','=',item.name),('state','!=','cancel')])
                
                
                comu_released = all_released.filtered(lambda pr: pr.date_order.date() <= full_date.date() and pr.date_order.date() >= first_day_of_m.date())#.month == int(month_) and pr.date_order.year == year and pr.date_order.day <= day

                if full_date.date() == in_pr.production_date.date():
                    comu_pcs = in_pr.production_till_date

                cm_pcs = 0
                cm_rel = sum(comu_released.mapped('product_uom_qty'))
                if full_date.date() > in_pr.production_date.date():
                    comu_day_outputs = comu_outputs.filtered(lambda pr: pr.action_date.date() > in_pr.production_date.date() and pr.action_date.date() <= full_date.date())
                    # cm_day_released = comu_released.filtered(lambda pr: pr.date_order.date() > in_pr.production_date.date())
                    
                    cm_pcs = sum(comu_day_outputs.mapped('qty'))
                    comu_pcs = in_pr.production_till_date + cm_pcs

                price = total_qty = comur_value = pending_pcs = 0
                
                if comu_released:
                    comur_value = round(sum(comu_released.mapped('sale_order_line.price_subtotal')),2)
                    total_qty = sum(comu_released.mapped('sale_order_line.product_uom_qty'))
                    price = round((comur_value / total_qty),4)
                    # pending_pcs = total_qty - comu_pcs

                
                item_run_ord = running_orders.filtered(lambda pr: pr.fg_categ_type == item.name)
                
                invoiced = round((pack_pcs*price),2)
                # pending_usd = round((pending_pcs*price),2)
                comu_inv = round((comu_pcs*price),2)


                pending_oa = all_released.filtered(lambda pr: (pr.date_order.date() <= full_date.date() and  (pr.closing_date != True or pr.closing_date.date() > full_date.date())))


                query = """ select count(distinct a.oa_id) oa_count,sum(a.product_uom_qty) qty,avg(a.price_unit) price,ARRAY_AGG(distinct a.oa_id) oa_ids  from manufacturing_order as a inner join sale_order as s on a.oa_id=s.id where date(s.date_order) <= %s and (a.closing_date is null or date(a.closing_date) > %s) and a.fg_categ_type = %s """
                self.env.cr.execute(query, (full_date.date(),full_date.date(),item.name))
                get_pending = self.env.cr.fetchone()

                
                # pending_oa = all_released.filtered(lambda pr: (pr.date_order.date() <= full_date.date() and  (pr.closing_date != True or (getattr(pr.closing_date, 'date', lambda: None)() == True and pr.closing_date.date() > full_date.date()) ) ))
                
                pending_ids = 0
                
                if len(get_pending) > 1:
                    # raise UserError((get_pending[0],get_pending[1],get_pending[3]))
                    # oa_ids = pending_oa.mapped('oa_id')
                    pending_oa_ids = None
                    pending_oa_ids = get_pending[3]
                    if pending_oa_ids:
                        pending_oa_ids = set(get_pending[3])
                        #pending_oa.mapped('oa_id.id')
                        pending_oa_ids = ','.join([str(i) for i in sorted(pending_oa_ids)])
                        pending_oa_ids = [int(i) for i in sorted(pending_oa_ids.split(','))]
                    # raise UserError((pending_oa_ids))
                        pending_ids = get_pending[0]
                        qty = get_pending[1]#sum(pending_oa.mapped('product_uom_qty'))
                        price = get_pending[2]
                        
                        _outputs = all_outputs.filtered(lambda pr: (pr.action_date.date() <= full_date.date() and  pr.fg_categ_type == item.name and pr.oa_id.id in pending_oa_ids))
                        if _outputs:
                            # raise UserError(('fefef'))
                            doneqty = sum(_outputs.mapped('qty'))
                            pending_pcs = qty - doneqty
                            pending_usd = round((pending_pcs * price),2)
                
                if start_time.date() == full_date.date():
                    # raise UserError((start_time.date(),full_date.date()))
                    pending_pcs = sum(item_run_ord.mapped('balance_qty'))
                    oa_ids = item_run_ord.mapped('oa_id')
                    pending_ids = len(oa_ids)
                    # pending_ids = sum(item_run_ord.mapped('balance_qty'))
                    
                    vl = round(sum(item_run_ord.mapped('sale_order_line.price_subtotal')),2)
                    _qty = sum(item_run_ord.mapped('sale_order_line.product_uom_qty'))
                    if _qty > 0 and pending_pcs > 0:
                        price = round((vl / _qty),4)
                        pending_usd = round((pending_pcs*price),2)

                closed_oa = all_released.filtered(lambda pr: pr.date_order.date() <= full_date.date() and  pr.closing_date != False)
                if closed_oa:
                    closed_oa = closed_oa.filtered(lambda pr: pr.closing_date.date() == full_date.date())
                
                if closed_oa:
                    oa_ids = closed_oa.mapped('oa_id')
                    closed_ids += len(oa_ids)
                
                today_released = all_released.filtered(lambda pr: pr.date_order.date() == full_date.date())
                tr_value = round(sum(today_released.mapped('sale_order_line.price_subtotal')),2)
                
                if full_date.date() == in_pr.production_date.date():
                    comu_inv = in_pr.invoice_till_date
                    # comur_value = in_pr.released_till_date
                    
                if full_date.date() > in_pr.production_date.date():
                    cm_inv = price * cm_pcs
                    cmr_val = cm_rel * price
                    comu_inv = in_pr.invoice_till_date + cm_inv
                    # comur_value = in_pr.released_till_date + cmr_val
                
                order_data = []
                
                invoiced = round(invoiced,0)
                pending_usd = round(pending_usd,0)
                comu_inv = round(comu_inv,0)
                tr_value = round(tr_value,0)
                comur_value = round(comur_value,0)
                
                if start_time.date() < full_date.date():
                    invoiced = pending_usd = comu_inv = tr_value = comur_value = pack_pcs = pending_pcs = comu_pcs = pending_ids = None

                else:
                    if pack_pcs == 0:
                        pack_pcs = None
                    if pending_pcs <= 0:
                        pending_pcs = None,
                        pending_usd = None,
                    if comu_pcs == 0:
                        comu_pcs = None
                    if pending_ids == 0:
                        pending_ids = None
    
                    if invoiced == 0:
                        invoiced = None
                    # if pending_usd == 0:
                    #     pending_usd = None,
                    if comu_inv == 0:
                        comu_inv = None
                    if tr_value == 0:
                        tr_value = None    
                    if comur_value == 0:
                        comur_value = None
                
                order_data = [
                    item.name,
                    pack_pcs,
                    invoiced,
                    pending_pcs,
                    pending_usd,
                    comu_pcs,
                    comu_inv,
                    tr_value,
                    comur_value,
                    pending_ids,
                    ]
                report_data.append(order_data)
            
            row = 1
            
            for line in report_data:
                col = 0
                for l in line:
                    if col in (2,4,6,7,8):
                        sheet.write(row, col, l, format_label_2)
                    else:
                        sheet.write(row, col, l, format_label_1)
                    col += 1
                row += 1

            sheet.write(row, 0, 'Total Order Close :', format_label_1)
            sheet.write(row, 1, closed_ids, format_label_1)
            sheet.write(row, 2, '', format_label_1)
            sheet.write(row, 3, '', format_label_1)
            sheet.write(row, 4, '', format_label_1)
            sheet.write(row, 5, '', format_label_1)
            sheet.write(row, 6, '', format_label_1)
            sheet.write(row, 7, '', format_label_1)
            sheet.write(row, 8, '', format_label_1)
            sheet.write(row, 9, '', format_label_1)
            row += 1    
            sheet.write(row, 0, 'TOTAL', row_style)
            sheet.write(row, 1, '=SUM(B{0}:B{1})'.format(1, row-1), row_style)
            sheet.write(row, 2, '=SUM(C{0}:C{1})'.format(1, row), _row_style)
            sheet.write(row, 3, '=SUM(D{0}:D{1})'.format(1, row), row_style)
            sheet.write(row, 4, '=SUM(E{0}:E{1})'.format(1, row), _row_style)
            sheet.write(row, 5, '=SUM(F{0}:F{1})'.format(1, row), row_style)
            sheet.write(row, 6, '=SUM(G{0}:G{1})'.format(1, row), _row_style)
            sheet.write(row, 7, '=SUM(H{0}:H{1})'.format(1, row), _row_style)
            sheet.write(row, 8, '=SUM(I{0}:I{1})'.format(1, row), _row_style)
            sheet.write(row, 9, '=SUM(J{0}:J{1})'.format(1, row), row_style)

            # if start_time.day == day and start_time.month == int(month_):
            #     sheet.Activate()
        # raise UserError(())
        # workbook.active =  start_time.day  
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Invoice')),
            'target': 'self',
        }

    def daily_closed_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        month_ = None
        if data.get('month_list'):
            month_ = data.get('month_list')
        year = datetime.today().year


        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        column_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center'})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        all_released = self.env['manufacturing.order'].search([('state','=','closed'),('closing_date','!=',False)])
        all_items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
        for day in self.iterate_days(year, int(month_)):
            report_name = day
            
            full_date = fields.datetime.now().replace(day = 1).replace(month = int(month_)).replace(year = year)
            full_date = full_date.replace(day = day)

            sheet = workbook.add_worksheet(('%s' % (report_name)))

            if start_time.date() == full_date.date():
                sheet.activate()
            
            report_data = []
            closed_ids = 0

            # if all_released:
            #     raise UserError((all_released[0].closing_date.date(),full_date.date()))
            datewise_released = all_released.filtered(lambda pr: pr.closing_date.date() == full_date.date())

            if datewise_released:
                # item_list = ','.join([str(i) for i in datewise_released.fg_categ_type])
                item_list = datewise_released.mapped('fg_categ_type')
                # item_list = [str(i) for i in sorted(item_list.split(','))]
                # raise UserError((item_list))
                items = all_items.filtered(lambda pr: pr.name in (item_list))
                items = items.sorted(key=lambda pr: pr.sequence)
                cl_num = 0
                for item in items:
                    # raise UserError(('item_list'))
                    report_data = []
                    sheet.write(0, cl_num, item.name, column_style)
                    sheet.set_column(cl_num, cl_num, 20)
                    
                    closed_oa = datewise_released.filtered(lambda pr: pr.fg_categ_type == item.name)
                    if closed_oa:
                        order_data = []
                        # closed_oa = closed_oa.mapped('oa_id')
                        sale_orders = self.env['sale.order'].browse(closed_oa.oa_id.ids).sorted(key=lambda pr: pr.id)
                        for oa in sale_orders:
                            order_data = [
                                oa.name,
                                ]
                            report_data.append(order_data)
                
                    row = 1
                    for line in report_data:
                        sheet.write(row, cl_num, line[0], format_label_1)
                        row += 1
                    
                    cl_num += 1

        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Production Report (FG)')),
            'target': 'self',
        }

    def packing_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        
        all_outputs = self.env['operation.details'].search([('next_operation','=','FG Packing')])
        all_outputs = all_outputs.filtered(lambda pr: pr.action_date.date() >= data.get('date_from') and pr.action_date.date() <= data.get('date_to'))
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center'})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'vcenter', 'align': 'center', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})#'num_format': '$#,##0'
            
        items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI'),('company_id','=',self.env.company.id)]).sorted(key=lambda pr: pr.sequence)
        
        report_data = []
        
        for item in items:
            report_data = []
            itemwise_outputs = all_outputs.filtered(lambda pr: pr.fg_categ_type == item.name).sorted(key=lambda pr: pr.action_date)
            if itemwise_outputs:
                sheet = workbook.add_worksheet(('%s' % (item.name)))
                sheet.freeze_panes(1, 0)
                
                sheet.write(0, 0, "DATE", column_style)
                sheet.write(0, 1, "OA", column_style)
                sheet.write(0, 2, "SHADE", column_style)
                sheet.write(0, 3, "TZP", column_style)
                sheet.write(0, 4, "STOPPER", column_style)
                sheet.write(0, 5, "SIZE", column_style)
                sheet.write(0, 6, "QTY", column_style)
                sheet.write(0, 7, "PACKET", column_style)
                sheet.write(0, 8, "REMARK", column_style)
                sheet.write(0, 9, "PAGE NO", column_style)
                sheet.write(0, 10, "TABLE", column_style)
    
                sheet.set_column(0, 0, 15)
                sheet.set_column(1, 1, 15)
                sheet.set_column(2, 2, 25)
                sheet.set_column(2, 3, 25)
                # sheet.set_column(3, 3, 15)
                # sheet.set_column(4, 4, 15)
                # sheet.set_column(5, 5, 15)
                # sheet.set_column(6, 6, 15)
                # sheet.set_column(7, 7, 15)
                # sheet.set_column(8, 8, 15)
                
                order_data = []
                for i in itemwise_outputs:
                    order_data = []
                    slider = stopper = sizes = None
                    
                    sizes = i.sizein
                    if sizes == "N/A":
                        sizes = i.sizecm

                    findslider = i.slidercodesfg.find("TZP ")
                    if findslider > 0:
                        slider = i.slidercodesfg.split("TZP ",1)[1]
                    else:
                        slider = i.slidercodesfg.split("TZP-",1)[1]
                    if i.mrp_line.topbottom:
                        stopper = i.mrp_line.topbottom
                    
                    order_data = [
                        i.action_date.strftime("%d-%b-%Y"),
                        i.oa_id.name,
                        i.shade,
                        slider,
                        stopper,
                        sizes,
                        i.qty,
                        i.pack_qty,
                        '',
                        '',
                        '',
                        ]
                    report_data.append(order_data)
            row = 1
            for line in report_data:
                col = 0
                for l in line:
                    sheet.write(row, col, l, format_label_1)
                    col += 1
                row += 1

        
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Packing Production Report')),
            'target': 'self',
        }