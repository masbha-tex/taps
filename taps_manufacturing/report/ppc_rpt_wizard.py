import base64
import io
from datetime import date
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
        if self.report_type == "all":
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
            
            sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
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
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(0, 1, 0)
            sheet.set_column(0, 2, 20)
            sheet.set_column(0, 3, 20)
            sheet.set_column(0, 4, 20)
            sheet.set_column(0, 5, 20)
            sheet.set_column(0, 6, 20)
            sheet.set_column(0, 7, 20)

            sheet.set_row(0, 30)
            mrp_datas = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('balance_qty','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id),('fg_categ_type','=',item.name)]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id')
            # all_oa = set(mrp_datas.mapped('oa_id'))
            
            row = 1
            for oa in all_oa:
                o_data = mrp_datas.filtered(lambda pr: pr.oa_id.id == oa.id)
            # for orders in sale_orders:
            #     docs = self.env['sale.order.line'].search([('order_id', '=', orders)])
                # raise UserError((oa.name))
                # all_sliders = sliders.mapped('slidercodesfg')
                # for slider in all_sliders:
                #     # raise UserError((slider))
                #     docs = sliders.filtered(lambda pr: pr.slidercodesfg == slider)
                # if o_data:
                #     raise UserError(('slider'))
                col = 0
                for l in range(15):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, o_data[0].oa_id.name.replace("OA", ""), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        # sheet.write(row, col, format_custom_date(o_data[0].oa_id.create_date), row_style)
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        slider_code = o_data[0].slidercodesfg.split()[-1]
                        sheet.write(row, col,slider_code, row_style)
                    elif col == 5:
                        # sheet.write(row, col, format_custom_date(o_data[0].dyeing_plan), row_style)
                        sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        sheet.write(row, col, sum(o_data.mapped('dyeing_qc_pass')), row_style) #Shade ok
                    elif col == 7:
                        sheet.write(row, col, sum(o_data.mapped('plating_output')), row_style) #slider plating ok
                    elif col == 8:
                        sheet.write(row, col, '', row_style)
                    elif col == 9:
                        sheet.write(row, col, sum(o_data.mapped('product_uom_qty')), row_style)
                    elif col == 10:
                        sheet.write(row, col,sum( o_data.mapped('done_qty')) , row_style)
                    elif col == 11:
                        sheet.write(row, col, sum(o_data.mapped('balance_qty')), row_style)
                    elif col == 12:
                        oa_create_date = o_data[0].oa_id.create_date
                        today = datetime.now().date()
                        date_difference = today - oa_create_date.date()
                        
                        sheet.write(row, col, date_difference, row_style) #lead Time
                    elif col == 13:
                        sheet.write(row, col, o_data[0].oa_id.buyer_name.name, row_style)
                    elif col == 14:
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style)
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
        
