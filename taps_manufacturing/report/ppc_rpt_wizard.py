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


class PpcReportWizard(models.TransientModel):
    _name = 'ppc.report'
    _description = 'PPC Reports'
    _check_company_auto = True
    
    is_company = fields.Boolean(readonly=False, default=False)
    
    report_category = fields.Selection([('pw','Product Wise Production Summery'),
                                        ('bw','Buyer Wise Production Summery'),
                                        ('cw','Customer Wise Production Summery'),
                                        ('tw','Team Wise Production Summery'),
                                        ('stw','Stopper Wise Production Summery'),
                                        ('tzpw','TZP Wise Production Summery'),
                                        ('oth','Others Report')],
                                      string='Report Category', required=True, help='Report Category', default='pw'
                                      )

    report_type = fields.Selection(
        [('all', 'All Item'), ('m4', 'Metal 4'), ('m5all', 'Metal 5 All'),
         ('m5oe', 'Metal 5 Open END'), ('m5ce', 'Metal 5 Close END'),
         ('c3', 'Coil 3'), ('c3inv', 'Coil 3 INVIABLE'), ('c5all', 'Coil 5 All'),
         ('c5oe', 'Coil 5 Open END'), ('c5ce', 'Coil 5 Close END'),
         ('p3', 'Plastic 3'), ('p5all', 'Plastic 5 All'), ('p5oe', 'Plastic 5 Open END'),
         ('p5ce', 'Plastic 5 Close END'), ('others', 'Others Item')],
        string='Report Type', required=True, help='Report Type', default='all'
    )

    
    date_from = fields.Date('Date from', readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', readonly=False, default=lambda self: self._compute_to_date())
    
    month_list = fields.Selection('_get_month_list', 'Month') #, default=lambda self: self._get_month_list()

    file_data = fields.Binary(readonly=True, attachment=False)



    @api.depends('date_from')
    def _compute_from_date(self):
        dt_from = fields.datetime.now().replace(day = 1)
        return dt_from

    @api.depends('date_to')
    def _compute_to_date(self):
        # last_day_of_month = calendar.monthrange(fields.datetime.now().year, fields.datetime.now().month)[1]
        dt_to = fields.datetime.now()#.replace(day = last_day_of_month)
        return dt_to

    

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
        if self.report_type == "m4":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            if self.env.company.id == 1:
                return self.iteam_wise_all(self, data=data)
            if self.env.company.id == 3:
                return self.pi_mt_xls_template(self, data=data)
        if self.report_type == "all":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            return self.all_iteam_xls(self, data=data)
        if self.report_type == "pis":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
            return self.daily_pr_xls_template(self, data=data)
        if self.report_type == "dpcl":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
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

      #Iteam_wise all
    def iteam_wise_all(self, docids, data=None):
        start_time = fields.datetime.now()
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])

        m_orders = running_orders.search([('revision_no','=',None)])
        
        rev_orders = running_orders - m_orders
        
        m_orders = running_orders
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        red_fill_format = workbook.add_format({'bg_color': '#A7A7A7', 'align': 'center', 'valign': 'vcenter','left': True, 'top': True, 'right': True, 'bottom': True})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16,'valign': 'vcenter','align': 'center', 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top','align': 'left', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})

        format_label_5 = workbook.add_format({'font':'Arial', 'font_size': 13, 'valign': 'vcenter','align': 'center', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})
        
      

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
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type.name == item.name)
            
            # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = item.name
            # raise UserError((items))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
                
            if report_name == 'M#4 CE':
                sheet.set_tab_color('#0000FE')
            if report_name == 'M#5 CE':
                sheet.set_tab_color('#C00000')
            if report_name == 'M#5 OE':
                sheet.set_tab_color('#FF0000')
            if report_name == 'C#3 CE':
                sheet.set_tab_color('#974706')
            if report_name == 'C#3 Inv CE':
                sheet.set_tab_color('#92D050')
            if report_name == 'C#5 CE':
                sheet.set_tab_color('#FFC000')
            if report_name == 'C#5 OE':
                sheet.set_tab_color('#FFFF00')
            if report_name == 'P#3 CE':
                sheet.set_tab_color('#002060')
            if report_name == 'P#3 OE':
                sheet.set_tab_color('#0070C0')
            if report_name == 'P#5 OE':
                sheet.set_tab_color('#0070C0')
            if report_name == 'P#5 CE':
                sheet.set_tab_color('#00B050')
           

            sheet.set_margins(left=0.2, right=0.3, top=0.2, bottom=0.2)
            sheet.set_footer('Iteam: &A Page: &P of &N Printed at &D &T', {'margin': 0.08, 'align': 'center', 'font_size': 12})
            # sheet.set_footer('Page: &P of &N','Printed at &D &T', {'margin': 0.08, 'align': 'right', 'font_size': 10})
            
            sheet.fit_to_pages(1, 0)
            sheet.set_zoom(75)
            sheet.freeze_panes(1, 0)
            sheet.set_paper(9)
            
            sheet.write(0, 0, "Sl. No", column_style)
            # sheet.write(0, 1, f"PRODUCT: {report_name}", column_style)
            sheet.write(0, 1, "PI NO", column_style)
            sheet.write(0, 2, "OA NO", column_style)
            sheet.write(0, 3, "OA DATE", column_style)
            sheet.write(0, 4, "SLIDER/PCS", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "REMARKS", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
           
            sheet.set_column(0, 15, 20)

            sheet.set_row(0, 30)
            docs = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('balance_qty','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            for o_data in docs:
                col = 0
                row = 1
                for l in range(17):
                    if col == 0:
                        sl_no = 1
                        sheet.write(row, col, sl_no, row_style)
                        sl_no +=1
                    elif col == 1:
                        sheet.write(row, col, o_data.oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, o_data.oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data.oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        sheet.write(row, col, o_data.slidercodesfg, row_style)
                    elif col == 5:
                        sheet.write(row, col, o_data.dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        sheet.write(row, col, o_data.dyeing_qc_pass, row_style) #Shade ok
                    elif col == 7:
                        sheet.write(row, col, o_data.plating_output, row_style) #slider plating ok
                    elif col == 8:
                        sheet.write(row, col, '', row_style)
                    elif col == 9:
                        sheet.write(row, col, o_data.product_uom_qty, row_style)
                    elif col == 10:
                        sheet.write(row, col, o_data.done_qty , row_style)
                    elif col == 11:
                        sheet.write(row, col, o_data.balance_qty , row_style)
                    elif col == 12:
                        oa_create_date = o_data.oa_id.create_date
                        today = datetime.now().date()
                        date_difference = today - oa_create_date.date()
                        
                        sheet.write(row, col, date_difference, row_style) #lead Time
                    elif col == 13:
                        sheet.write(row, col, o_data.oa_id.buyer_name.name, row_style)
                    elif col == 14:
                        sheet.write(row, col, o_data.oa_id.partner_id.name, row_style)
                    # elif col == 14:
                    #     sheet.write(row, col, o_data.expected_date.strftime("%d/%m/%Y"), row_style)
    
    
                    #sheet.set_column(0, 0, 15)
                    col += 1
                row += 1
                

                            

             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('All Item')),
            'target': 'self',
        }
        
    def all_iteam_xls(self, docids, data=None):
        start_time = fields.datetime.now()
        # domain = []
        # if data.get('date_from'):
        #     domain.append(('date_from', '=', data.get('date_from'))) 
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
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
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        red_fill_format = workbook.add_format({'bg_color': '#A7A7A7', 'align': 'center', 'valign': 'vcenter','left': True, 'top': True, 'right': True, 'bottom': True})
        
        
        # column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16,'valign': 'vcenter','align': 'center', 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top','align': 'left', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})

        format_label_5 = workbook.add_format({'font':'Arial', 'font_size': 13, 'valign': 'vcenter','align': 'center', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})
        
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
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type.name == item.name)
            
            sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = item.name
            # raise UserError((items))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
            
            # for row_num in range(1, 50000):  
            #     sheet.set_row(row_num, 32)
                
            if report_name == 'M#4 CE':
                sheet.set_tab_color('#0000FE')
            if report_name == 'M#5 CE':
                sheet.set_tab_color('#C00000')
            if report_name == 'M#5 OE':
                sheet.set_tab_color('#FF0000')
            if report_name == 'C#3 CE':
                sheet.set_tab_color('#974706')
            if report_name == 'C#3 Inv CE':
                sheet.set_tab_color('#92D050')
            if report_name == 'C#5 CE':
                sheet.set_tab_color('#FFC000')
            if report_name == 'C#5 OE':
                sheet.set_tab_color('#FFFF00')
            if report_name == 'P#3 CE':
                sheet.set_tab_color('#002060')
            if report_name == 'P#3 OE':
                sheet.set_tab_color('#0070C0')
            if report_name == 'P#5 OE':
                sheet.set_tab_color('#0070C0')
            if report_name == 'P#5 CE':
                sheet.set_tab_color('#00B050')
           

            sheet.set_margins(left=0.2, right=0.3, top=0.2, bottom=0.2)
            sheet.set_footer('Iteam: &A Page: &P of &N Printed at &D &T', {'margin': 0.08, 'align': 'center', 'font_size': 12})
            # sheet.set_footer('Page: &P of &N','Printed at &D &T', {'margin': 0.08, 'align': 'right', 'font_size': 10})
            
            sheet.fit_to_pages(1, 0)
            sheet.set_zoom(75)
            sheet.freeze_panes(1, 0)
            sheet.set_paper(9)
            
            sheet.write(0, 0, "Sl. No", column_style)
            # sheet.write(0, 1, f"PRODUCT: {report_name}", column_style)
            sheet.write(0, 1, "PI NO", column_style)
            sheet.write(0, 2, "OA NO", column_style)
            sheet.write(0, 3, "OA DATE", column_style)
            sheet.write(0, 4, "SLIDER/PCS", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "REMARKS", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
           
            sheet.set_column(0, 15, 20)
            
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
                        payment_term = (orders.payment_term_id.name or '')
                        customer = "\n".join([orders.partner_id.name,"\n",orders.buyer_name.name,"\n",payment_term])
                        pi_num = orders.order_ref.pi_number
                        oa_num = int(orders.name.replace('OA',''))
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
                    # if o_data.numberoftop:
                    #     pr_name = "\n".join([pr_name,o_data.numberoftop])
                    # if o_data.ptopfinish:
                    #     pr_name = "\n".join([pr_name,o_data.ptopfinish])
                    # if o_data.pbotomfinish:
                    #     pr_name = "\n".join([pr_name,o_data.pbotomfinish])
                    # if o_data.ppinboxfinish:
                    #     pr_name = "\n".join([pr_name,o_data.ppinboxfinish])
                    # if o_data.topbottom:
                    #     pr_name = "\n".join([pr_name,o_data.topbottom])
                    slider = o_data.slidercodesfg
                    finish = o_data.finish #.replace('\n',' ')
                    shade = o_data.shade
                    # if shade:
                    #     shade = o_data.shade.replace('\n',' ')
                        # shade = re.sub(r'\n\s*\n', ' ', o_data.shade)
                    shadewise_tape = o_data.shadewise_tape
                    
                    sizein = o_data.sizein
                    sizecm = o_data.sizecm
                    if sizein == 'N/A':
                        sizein = ''
                    if sizecm == 'N/A':
                        sizecm = ''
                    
                    m_order = self.env['manufacturing.order'].search([('sale_order_line','=',o_data.id),('company_id','=',self.env.company.id)])
                    ready_qty = sum(m_order.mapped('done_qty'))
                    # raise UserError((o_data.id,ready_qty))
                    balance_qty = o_data.product_uom_qty - ready_qty
                    if ready_qty == 0:
                        ready_qty = None
                    if balance_qty == 0:
                        balance_qty = None
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
                    _top = self.env['operation.details'].search([('sale_line_of_top','=',o_data.id),('company_id','=',self.env.company.id)])
                    if _top:
                        order_data = [
                            customer,
                            'TOP',
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
                            _top.qty,
                            _top.done_qty,
                            _top.balance_qty,
                            0,
                            0,
                            0,
                            0,
                            0,
                            0,
                            #o_data.pinbox_con,
                            orders.sale_representative.name,
                        ]
                        report_data.append(order_data)
                # if _range > 0:
                #     _range += 2
                # _range += len(report_data)
                
                # sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
                # sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
                # sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
                # sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
                # sheet.merge_range(row_rang, 7, _range, 7, '', merge_format)
                # sheet.merge_range(row_rang, 8, _range, 8, '', merge_format)

                # # Set row height for the merged cells
                # for row_num in range(row_rang, _range + 1):
                #     sheet.set_row(row_num, 32)  # Adjust the height value as needed
                
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
                        elif col in(4,5,6):
                            sheet.write(row, col, l, format_label_3)
                        elif col == 8:
                            sheet.write(row, col, l, format_label_4)
                        elif col == 9 :
                            # sheet.write(row, col, l, format_label_4)
                            if isinstance(l, bool):
                                l = str(l)
                            number_of_newlines = l.count('\n') if isinstance(l, str) else 0
                            if number_of_newlines > 2: 
                                row_height = number_of_newlines * 12
                                sheet.write(row, col, l, format_label_4)
                                sheet.set_row(row, row_height)
                            else :
                                row_height = 32
                                sheet.write(row, col, l, format_label_4)
                                sheet.set_row(row, row_height)
                        elif col in(10,11,12,13):
                            sheet.write(row, col, l, format_label_5)
                        elif col == 14:
                            if l:
                                sheet.write(row, col,l, row_style_sum)#'=M{1}-N{1}'.format(row + 1)
                            else:
                                sheet.write(row, col, l, red_fill_format)
                                
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

                    # Set the row height dynamically based on the content
                    # # if col == 9:
                    # max_height = max(len(str(line[col])) for col in range(len(line)))
                    # sheet.set_row(row, max(32, max_height*1.2))  # Adjust the multiplier as needed
                    
                    row += 1
                    inline_row += 1
                    row_p = row_sl = row_f = row_sh = inline_row - 1
                
                sheet.write(row, 0, '',row_style_border_left)
                sheet.write(row, 1, '',row_style_border_top_bottom)
                sheet.write(row, 2, '',row_style_border_top_bottom)
                sheet.write(row, 3, '',row_style_border_top_bottom)
                sheet.write(row, 4, '',row_style_border_top_bottom)
                sheet.write(row, 5, '',row_style_border_top_bottom)
                sheet.write(row, 6, '',row_style_border_top_bottom)
                sheet.write(row, 7, '',row_style_border_top_bottom)
                sheet.write(row, 8, '',row_style_border_top_bottom)
                sheet.write(row, 9, '',row_style_border_top_bottom)
                sheet.write(row, 10, '',row_style_border_top_bottom)
                sheet.write(row, 11, '',row_style_border_top_bottom)
                sheet.write(row, 12, '=SUM(M{0}:M{1})'.format(row_rang+1, row), row_style_sum)
                sheet.write(row, 13, '=SUM(N{0}:N{1})'.format(row_rang+1, row), row_style_sum)
                sheet.write(row, 14, '=M{1}-N{1}'.format(row+1, row+1), row_style_sum)
                sheet.write(row, 15, '',row_style_border_top_bottom)
                # sheet.write(row, 16, shade_total, row_style)
                # sheet.write(row, 17, wire_total, row_style)
                # sheet.write(row, 18, slider_total, row_style)
                # sheet.write(row, 19, bottom_total, row_style)
                # sheet.write(row, 20, top_total, row_style)
                # sheet.write(row, 21, '',row_style_border_right)

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
            sheet.write(row+1, 12, '')
            sheet.write(row+1, 13, '')
            sheet.write(row+1, 14, '')
            sheet.write(row+1, 15, '')
            sheet.write(row+1, 16, '')
            sheet.write(row+1, 17, '')
            sheet.write(row+1, 18, '')
            sheet.write(row+1, 19, '')
            sheet.write(row+1, 20, '')
            sheet.write(row+1, 21, '')
            row += 1
            sheet.write(row+1, 0, '',row_style_border_top_bottom)
            sheet.write(row+1, 1, '',row_style_border_top_bottom)
            sheet.write(row+1, 2, '',row_style_border_top_bottom)
            sheet.write(row+1, 3, '',row_style_border_top_bottom)
            sheet.write(row+1, 4, '',row_style_border_top_bottom)
            sheet.write(row+1, 5, '',row_style_border_top_bottom)
            sheet.write(row+1, 6, '',row_style_border_top_bottom)
            sheet.write(row+1, 7, '',row_style_border_top_bottom)
            sheet.write(row+1, 8, '',row_style_border_top_bottom)
            sheet.write(row+1, 9, '',row_style_border_top_bottom)
            sheet.write(row+1, 10, '',row_style_border_top_bottom)
            sheet.write(row+1, 11, '',row_style_border_top_bottom)
            sheet.write(row+1, 12, '=SUM(M{0}:M{1})/2'.format(1, row_rang-1), row_style_sum)
            sheet.write(row+1, 13, '=SUM(N{0}:N{1})/2'.format(1, row_rang-1), row_style_sum)
            sheet.write(row+1, 14, '=M{1}-N{1}'.format(row_rang+1, row_rang+1), row_style_sum)
            sheet.write(row+1, 15, '',row_style_border_top_bottom)
            sheet.write(row+1, 16, '',row_style_border_top_bottom)
            sheet.write(row+1, 17, '',row_style_border_top_bottom)
            sheet.write(row+1, 18, '',row_style_border_top_bottom)
            sheet.write(row+1, 19, '',row_style_border_top_bottom)
            sheet.write(row+1, 20, '',row_style_border_top_bottom)
            sheet.write(row+1, 21, '',row_style_border_top_bottom)


        # sheet.conditional_format('O2:O1000', {'type':   'blanks','format': red_fill_format})
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('All Item Test')),
            'target': 'self',
        }

 