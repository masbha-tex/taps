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
        [('pw','Product Wise Production Summery'),
         ('bw','Buyer Wise Production Summery'),
         ('cw','Customer Wise Production Summery'),
         ('tw','Team Wise Production Summery'),
         ('stw','Stopper Wise Production Summery'),
         ('tzpw','TZP Wise Production Summery')],
        string='Report Type', required=True, help='Report Type', default='pw'
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
        if self.report_type == "pw":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            if self.env.company.id == 1:
                return self.iteam_wise_all(self, data=data)
            if self.env.company.id == 3:
                return self.pi_mt_xls_template(self, data=data)
        if self.report_type == "tw":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            return self.team_wise_all(self, data=data)
        if self.report_type == "bw":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
            return self.buyer_wise_all(self, data=data)
        if self.report_type == "cw":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
            return self.customer_wise_all(self, data=data)
        if self.report_type == "stw":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
            return self.stopper_wise_all(self, data=data)
        if self.report_type == "tzpw":
            data = {'month_list': self.month_list,'date_from': self.date_from,'date_to': self.date_to}
            return self.slider_wise_all(self, data=data)
            
        # if self.report_type in ("dppr", "pic"):
        #     if self.date_from == False or self.date_to == False:
        #         raise UserError(('Select From and To date'))
        #     elif self.date_from > self.date_to:
        #         raise UserError(('From date must be less then To date'))
        #     else:
        #         data = {'date_from': self.date_from,'date_to': self.date_to}
        #         if self.report_type == "pic":
        #             return self.closed_pi_xls_template(self, data=data)
        #         return self.packing_xls_template(self, data=data)

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
        
        row_style = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'center', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_ = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
  
      

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
            sheet.write(0, 4, "SLIDER", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK ", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "DIPPING", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
            sheet.write(0, 16, "REMARKS", column_style)
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(1, 1, 0)
            sheet.set_column(2, 2, 10)
            sheet.set_column(4, 4, 22)
            sheet.set_column(6, 6, 18)
            sheet.set_column(8, 8, 0)
            sheet.set_column(9, 11, 16)
            sheet.set_column(13, 13, 24)
            sheet.set_column(14, 14, 34)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 24)
           

            sheet.set_row(0, 32)
            sheet.set_row(1, 20)
            mrp_datas = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id),('fg_categ_type','=',item.name)]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id').sorted(key=lambda pr: pr.id)
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
                for l in range(17):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, str(o_data[0].oa_id.name.replace("OA00", "")), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d %b"), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        slider_code_match = re.search(r'TZP-\s*(.+)', str(o_data[0].slidercodesfg)) #after all part tzp
                        slider_part = slider_code_match.group(1) if slider_code_match else ''
                        if slider_part:
                            sheet.write(row, col, f"TZP-{slider_part}", row_style)
                        
                        
                        # slider_code_match = re.search(r'TZP-\s*([^\s]+)', str(o_data[0].slidercodesfg)) #after tzp number only 
                        # slider_part = slider_code_match.group(1) if slider_code_match else ''
                        # if slider_part:
                        #     sheet.write(row, col, f"TZP- {slider_part}", row_style)

                        # sheet.write(row, col,o_data[0].slidercodesfg, row_style)
                    elif col == 5:
                        dyeing_plan_date = o_data[0].dyeing_plan.strftime("%d %b") if o_data[0].dyeing_plan else ''
                        sheet.write(row, col, dyeing_plan_date, row_style)                     
                        # sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        total_shade = round(sum(o_data.mapped('tape_con')), 2)
                        dyed_shade = round(sum(o_data.mapped('dyeing_qc_pass')), 2)
                        sheet.write(row, col, f"{dyed_shade} of {total_shade}", row_style)
                        # sheet.write(row, col, dyed_shade, row_style) 
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
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style_)
                    elif col == 15:
                        # raise UserError((o_data[0].exp_close_date))
                        exp_close_date = o_data[0].exp_close_date.strftime("%d %b") if o_data[0].exp_close_date else ''
                        sheet.write(row, col, exp_close_date, row_style)
                    elif col == 16:
                        sheet.write(row, col, '', row_style)

                    col += 1
                row += 1
            sum_start_row = 2
            sum_end_row = row 
            row += 1
            sheet.write(row, 0, '',row_style_border_top_bottom)
            sheet.write(row, 1, '',row_style_border_top_bottom)
            sheet.write(row, 2, '',row_style_border_top_bottom)
            sheet.write(row, 3, '',row_style_border_top_bottom)
            sheet.write(row, 4, '',row_style_border_top_bottom)
            sheet.write(row, 5, '',row_style_border_top_bottom)
            sheet.write(row, 6, '',row_style_border_top_bottom)
            sheet.write(row, 7, '',row_style_border_top_bottom)
            sheet.write(row, 8, '',row_style_border_top_bottom)
            sheet.write(row, 9, f'=SUM(J{sum_start_row}:J{sum_end_row})', row_style_sum)
            sheet.write(row, 10, f'=SUM(K{sum_start_row}:K{sum_end_row})', row_style_sum)
            sheet.write(row, 11, f'=SUM(L{sum_start_row}:L{sum_end_row})', row_style_sum)
            sheet.write(row, 12, '',row_style_border_top_bottom)
            sheet.write(row, 13, '',row_style_border_top_bottom)
            sheet.write(row, 14, '',row_style_border_top_bottom)            
            sheet.write(row, 15, '',row_style_border_top_bottom)
            sheet.write(row, 16, '',row_style_border_top_bottom)
            
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Item Wise')),
            'target': 'self',
        }
        #iteam wise all end here 
    
        #team wise all started 
    def team_wise_all(self, docids, data=None):
        start_time = fields.datetime.now()
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
        
        m_orders = running_orders.search([('revision_no','=',None)])
        rev_orders = running_orders - m_orders
        m_orders = running_orders
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        
        row_style = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'center', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_left = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_ = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
  
        teams = self.env['crm.team'].search([('id','in',m_orders.oa_id.team_id.ids)]).sorted(key=lambda pr: pr.sequence)

        for team in teams:
            all_orders = None
            all_orders = self.env['sale.order'].browse(m_orders.oa_id.ids)
            all_orders = all_orders.filtered(lambda pr: pr.team_id.id == team.id).sorted(key=lambda pr: pr.id)        
            
            # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = team.name
            # raise UserError((teams))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
  
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
            sheet.write(0, 4, "SLIDER", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK ", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "DIPPING", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
            sheet.write(0, 16, "REMARKS", column_style)
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(1, 1, 0)
            sheet.set_column(2, 2, 10)
            sheet.set_column(4, 4, 45)
            sheet.set_column(6, 6, 18)
            sheet.set_column(4, 4, 22)
            sheet.set_column(8, 8, 0)
            sheet.set_column(9, 11, 16)
            sheet.set_column(13, 13, 24)
            sheet.set_column(14, 14, 34)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 24)
           

            sheet.set_row(0, 32)
            sheet.set_row(1, 20)
            mrp_datas = self.env['manufacturing.order'].search([
                ('oa_total_balance', '>', 0),
                ('oa_id', '!=', None),
                ('state', 'not in', ('closed', 'cancel')),
                ('company_id', '=', self.env.company.id),
                ('oa_id.team_id', '=', team.name)
            ]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id').sorted(key=lambda pr: pr.id)
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
                for l in range(17):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, str(o_data[0].oa_id.name.replace("OA00", "")), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d %b"), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        sheet.write(row, col, o_data[0].slidercodesfg, row_style_left)
                    elif col == 5:
                        dyeing_plan_date = o_data[0].dyeing_plan.strftime("%d %b") if o_data[0].dyeing_plan else ''
                        sheet.write(row, col, dyeing_plan_date, row_style)                     
                        # sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        total_shade = round(sum(o_data.mapped('tape_con')), 2)
                        dyed_shade = round(sum(o_data.mapped('dyeing_qc_pass')), 2)
                        sheet.write(row, col, f"{dyed_shade} of {total_shade}", row_style)
                        # sheet.write(row, col, dyed_shade, row_style) 
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
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style_)
                    elif col == 15:
                        # raise UserError((o_data[0].exp_close_date))
                        exp_close_date = o_data[0].exp_close_date.strftime("%d %b") if o_data[0].exp_close_date else ''
                        sheet.write(row, col, exp_close_date, row_style)
                    elif col == 16:
                        sheet.write(row, col, '', row_style)

                    col += 1
                row += 1
            sum_start_row = 2
            sum_end_row = row 
            row += 1
            sheet.write(row, 0, '',row_style_border_top_bottom)
            sheet.write(row, 1, '',row_style_border_top_bottom)
            sheet.write(row, 2, '',row_style_border_top_bottom)
            sheet.write(row, 3, '',row_style_border_top_bottom)
            sheet.write(row, 4, '',row_style_border_top_bottom)
            sheet.write(row, 5, '',row_style_border_top_bottom)
            sheet.write(row, 6, '',row_style_border_top_bottom)
            sheet.write(row, 7, '',row_style_border_top_bottom)
            sheet.write(row, 8, '',row_style_border_top_bottom)
            sheet.write(row, 9, f'=SUM(J{sum_start_row}:J{sum_end_row})', row_style_sum)
            sheet.write(row, 10, f'=SUM(K{sum_start_row}:K{sum_end_row})', row_style_sum)
            sheet.write(row, 11, f'=SUM(L{sum_start_row}:L{sum_end_row})', row_style_sum)
            sheet.write(row, 12, '',row_style_border_top_bottom)
            sheet.write(row, 13, '',row_style_border_top_bottom)
            sheet.write(row, 14, '',row_style_border_top_bottom)            
            sheet.write(row, 15, '',row_style_border_top_bottom)
            sheet.write(row, 16, '',row_style_border_top_bottom)
            
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Team Wise')),
            'target': 'self',
        }

    #team wise end here 

    # Buyer wise pending order start here 
    def buyer_wise_all(self, docids, data=None):
        start_time = fields.datetime.now()

        
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])

        m_orders = running_orders.search([('revision_no','=',None)])
        
        rev_orders = running_orders - m_orders
        
        m_orders = running_orders 
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        
        row_style = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'center', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_left = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_ = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
  
        buyers = self.env['res.partner'].search([('id','in',m_orders.oa_id.buyer_name.ids)])
        #.sorted(key=lambda pr: pr.sequence)

        for buyer in buyers:
            all_orders = None
            all_orders = self.env['sale.order'].browse(m_orders.oa_id.ids)
            all_orders = all_orders.filtered(lambda pr: pr.buyer_name.id == buyer.id).sorted(key=lambda pr: pr.id)        
            
            # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = buyer.name
            # raise UserError((buyers))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
  
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
            sheet.write(0, 4, "SLIDER", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK ", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "DIPPING", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
            sheet.write(0, 16, "REMARKS", column_style)
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(1, 1, 0)
            sheet.set_column(2, 2, 10)
            sheet.set_column(6, 6, 18)
            sheet.set_column(4, 4, 45)
            sheet.set_column(8, 8, 0)
            sheet.set_column(9, 11, 16)
            sheet.set_column(13, 13, 24)
            sheet.set_column(14, 14, 34)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 24)
           

            sheet.set_row(0, 32)
            sheet.set_row(1, 20)
            mrp_datas = self.env['manufacturing.order'].search([
                ('oa_total_balance', '>', 0),
                ('oa_id', '!=', None),
                ('state', 'not in', ('closed', 'cancel')),
                ('company_id', '=', self.env.company.id),
                ('oa_id.buyer_name', '=', buyer.name)
            ]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id').sorted(key=lambda pr: pr.id)
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
                for l in range(17):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, str(o_data[0].oa_id.name.replace("OA00", "")), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d %b"), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        sheet.write(row, col, o_data[0].slidercodesfg, row_style_left)
                    elif col == 5:
                        dyeing_plan_date = o_data[0].dyeing_plan.strftime("%d %b") if o_data[0].dyeing_plan else ''
                        sheet.write(row, col, dyeing_plan_date, row_style)                     
                        # sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        total_shade = round(sum(o_data.mapped('tape_con')), 2)
                        dyed_shade = round(sum(o_data.mapped('dyeing_qc_pass')), 2)
                        sheet.write(row, col, f"{dyed_shade} of {total_shade}", row_style)
                        # sheet.write(row, col, dyed_shade, row_style) 
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
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style_)
                    elif col == 15:
                        # raise UserError((o_data[0].exp_close_date))
                        exp_close_date = o_data[0].exp_close_date.strftime("%d %b") if o_data[0].exp_close_date else ''
                        sheet.write(row, col, exp_close_date, row_style)
                    elif col == 16:
                        sheet.write(row, col, '', row_style)

                    col += 1
                row += 1
            sum_start_row = 2
            sum_end_row = row 
            row += 1
            sheet.write(row, 0, '',row_style_border_top_bottom)
            sheet.write(row, 1, '',row_style_border_top_bottom)
            sheet.write(row, 2, '',row_style_border_top_bottom)
            sheet.write(row, 3, '',row_style_border_top_bottom)
            sheet.write(row, 4, '',row_style_border_top_bottom)
            sheet.write(row, 5, '',row_style_border_top_bottom)
            sheet.write(row, 6, '',row_style_border_top_bottom)
            sheet.write(row, 7, '',row_style_border_top_bottom)
            sheet.write(row, 8, '',row_style_border_top_bottom)
            sheet.write(row, 9, f'=SUM(J{sum_start_row}:J{sum_end_row})', row_style_sum)
            sheet.write(row, 10, f'=SUM(K{sum_start_row}:K{sum_end_row})', row_style_sum)
            sheet.write(row, 11, f'=SUM(L{sum_start_row}:L{sum_end_row})', row_style_sum)
            sheet.write(row, 12, '',row_style_border_top_bottom)
            sheet.write(row, 13, '',row_style_border_top_bottom)
            sheet.write(row, 14, '',row_style_border_top_bottom)            
            sheet.write(row, 15, '',row_style_border_top_bottom)
            sheet.write(row, 16, '',row_style_border_top_bottom)
            
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Buyer Wise')),
            'target': 'self',
        }

    # buyer wise end here 
    
    #Customer wise start here
    def customer_wise_all(self, docids, data=None):
        start_time = fields.datetime.now()

        
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])

        m_orders = running_orders.search([('revision_no','=',None)])
        rev_orders = running_orders - m_orders
        m_orders = running_orders 
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        
        row_style = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'center', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_left = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_ = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
  
        customers = self.env['res.partner'].search([('id','in',m_orders.oa_id.partner_id.ids)])
        #.sorted(key=lambda pr: pr.sequence)

        for customer in customers:
            all_orders = None
            all_orders = self.env['sale.order'].browse(m_orders.oa_id.ids)
            all_orders = all_orders.filtered(lambda pr: pr.partner_id.id == customer.id).sorted(key=lambda pr: pr.id)        
            
            # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = customer.name
            # raise UserError((buyers))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
  
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
            sheet.write(0, 4, "SLIDER", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK ", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "DIPPING", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
            sheet.write(0, 16, "REMARKS", column_style)
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(1, 1, 0)
            sheet.set_column(2, 2, 10)
            sheet.set_column(6, 6, 18)
            sheet.set_column(4, 4, 45)
            sheet.set_column(8, 8, 0)
            sheet.set_column(9, 11, 16)
            sheet.set_column(13, 13, 24)
            sheet.set_column(14, 14, 34)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 24)
           

            sheet.set_row(0, 32)
            sheet.set_row(1, 20)
            mrp_datas = self.env['manufacturing.order'].search([
                ('oa_total_balance', '>', 0),
                ('oa_id', '!=', None),
                ('state', 'not in', ('closed', 'cancel')),
                ('company_id', '=', self.env.company.id),
                ('oa_id.partner_id', '=', customer.name)
            ]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id').sorted(key=lambda pr: pr.id)
            # all_oa = set(mrp_datas.mapped('oa_id'))
            
            row = 1
            for oa in all_oa:
                o_data = mrp_datas.filtered(lambda pr: pr.oa_id.id == oa.id)
                col = 0
                for l in range(17):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, str(o_data[0].oa_id.name.replace("OA00", "")), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d %b"), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        sheet.write(row, col, o_data[0].slidercodesfg, row_style_left)
                    elif col == 5:
                        dyeing_plan_date = o_data[0].dyeing_plan.strftime("%d %b") if o_data[0].dyeing_plan else ''
                        sheet.write(row, col, dyeing_plan_date, row_style)                     
                        # sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        total_shade = round(sum(o_data.mapped('tape_con')), 2)
                        dyed_shade = round(sum(o_data.mapped('dyeing_qc_pass')), 2)
                        sheet.write(row, col, f"{dyed_shade} of {total_shade}", row_style)
                        # sheet.write(row, col, dyed_shade, row_style) 
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
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style_)
                    elif col == 15:
                        # raise UserError((o_data[0].exp_close_date))
                        exp_close_date = o_data[0].exp_close_date.strftime("%d %b") if o_data[0].exp_close_date else ''
                        sheet.write(row, col, exp_close_date, row_style)
                    elif col == 16:
                        sheet.write(row, col, '', row_style)

                    col += 1
                row += 1
            sum_start_row = 2
            sum_end_row = row 
            row += 1
            sheet.write(row, 0, '',row_style_border_top_bottom)
            sheet.write(row, 1, '',row_style_border_top_bottom)
            sheet.write(row, 2, '',row_style_border_top_bottom)
            sheet.write(row, 3, '',row_style_border_top_bottom)
            sheet.write(row, 4, '',row_style_border_top_bottom)
            sheet.write(row, 5, '',row_style_border_top_bottom)
            sheet.write(row, 6, '',row_style_border_top_bottom)
            sheet.write(row, 7, '',row_style_border_top_bottom)
            sheet.write(row, 8, '',row_style_border_top_bottom)
            sheet.write(row, 9, f'=SUM(J{sum_start_row}:J{sum_end_row})', row_style_sum)
            sheet.write(row, 10, f'=SUM(K{sum_start_row}:K{sum_end_row})', row_style_sum)
            sheet.write(row, 11, f'=SUM(L{sum_start_row}:L{sum_end_row})', row_style_sum)
            sheet.write(row, 12, '',row_style_border_top_bottom)
            sheet.write(row, 13, '',row_style_border_top_bottom)
            sheet.write(row, 14, '',row_style_border_top_bottom)            
            sheet.write(row, 15, '',row_style_border_top_bottom)
            sheet.write(row, 16, '',row_style_border_top_bottom)
            
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Customer Wise')),
            'target': 'self',
        }
    # Customer Wise end here

    #Stoper wise start here
    def stopper_wise_all(self, docids, data=None):
        start_time = fields.datetime.now()

        
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])

        m_orders = running_orders.search([('revision_no','=',None)])
        rev_orders = running_orders - m_orders
        m_orders = running_orders 
        # oa_total_balance revision_no
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 13,'bg_color': '#9BBB59','left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter','align': 'center','text_wrap':True})
        
        row_style = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'center', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_left = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_ = workbook.add_format({'bold': True,'valign': 'vcenter','align': 'left', 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
  
        
        #.sorted(key=lambda pr: pr.sequence)
        top_bottoms = m_orders.mapped('topbottom')

        for top_bottom in top_bottoms:
            all_orders = None
            raise UserError((top_bottom))
            # top_bottoms = self.env['sale.order.line'].search([('order_id','=',m_orders.oa_id),('topbottom','in',m_orders.topbottom)])
            all_orders = self.env['sale.order'].browse(m_orders.oa_id.ids)
            all_orders = all_orders.filtered(lambda pr: pr.oa_id.topbottom.id == top_bottom.id).sorted(key=lambda pr: pr.id)        
            
            # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
            
            report_name = top_bottom.name
            # raise UserError((buyers))
            
            sheet = workbook.add_worksheet(('%s' % (report_name)))
            sheet.set_default_row(30)
  
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
            sheet.write(0, 4, "SLIDER", column_style)
            sheet.write(0, 5, "DYE Plan DATE", column_style)
            sheet.write(0, 6, "SHADE OK ", column_style)
            sheet.write(0, 7, "SLIDR OK", column_style)
            sheet.write(0, 8, "DIPPING", column_style)
            sheet.write(0, 9, "ORDER QTY", column_style)
            sheet.write(0, 10, "READY QTY", column_style)
            sheet.write(0, 11, "PENDING", column_style)
            sheet.write(0, 12, "LEAD TIME", column_style)
            sheet.write(0, 13, "BUYER", column_style)
            sheet.write(0, 14, "CUSTOMER", column_style)
            sheet.write(0, 15, "CLOSING DATE", column_style)
            sheet.write(0, 16, "REMARKS", column_style)
           
            sheet.set_column(0, 0, 6)
            sheet.set_column(1, 1, 0)
            sheet.set_column(2, 2, 10)
            sheet.set_column(6, 6, 18)
            sheet.set_column(4, 4, 45)
            sheet.set_column(8, 8, 0)
            sheet.set_column(9, 11, 16)
            sheet.set_column(13, 13, 24)
            sheet.set_column(14, 14, 34)
            sheet.set_column(15, 15, 20)
            sheet.set_column(16, 16, 24)
           

            sheet.set_row(0, 32)
            sheet.set_row(1, 20)
            mrp_datas = self.env['manufacturing.order'].search([
                ('oa_total_balance', '>', 0),
                ('oa_id', '!=', None),
                ('state', 'not in', ('closed', 'cancel')),
                ('company_id', '=', self.env.company.id),
                ('oa_id.topbottom', '=', top_bottom.name)
            ]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)

            
            all_oa = mrp_datas.mapped('oa_id').sorted(key=lambda pr: pr.id)
            # all_oa = set(mrp_datas.mapped('oa_id'))
            
            row = 1
            for oa in all_oa:
                o_data = mrp_datas.filtered(lambda pr: pr.oa_id.id == oa.id)
                col = 0
                for l in range(17):
                    if col == 0:
                        sheet.write(row, col, row, row_style)
                    elif col == 1:
                        sheet.write(row, col, o_data[0].oa_id.order_ref.pi_number, row_style)
                    elif col == 2:
                        sheet.write(row, col, str(o_data[0].oa_id.name.replace("OA00", "")), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.name, row_style)
                    elif col == 3:
                        sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d %b"), row_style)
                        # sheet.write(row, col, o_data[0].oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                    elif col == 4:
                        sheet.write(row, col, o_data[0].slidercodesfg, row_style_left)
                    elif col == 5:
                        dyeing_plan_date = o_data[0].dyeing_plan.strftime("%d %b") if o_data[0].dyeing_plan else ''
                        sheet.write(row, col, dyeing_plan_date, row_style)                     
                        # sheet.write(row, col, o_data[0].dyeing_plan, row_style) #Dye Plan Date
                    elif col == 6:
                        total_shade = round(sum(o_data.mapped('tape_con')), 2)
                        dyed_shade = round(sum(o_data.mapped('dyeing_qc_pass')), 2)
                        sheet.write(row, col, f"{dyed_shade} of {total_shade}", row_style)
                        # sheet.write(row, col, dyed_shade, row_style) 
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
                        sheet.write(row, col, o_data[0].oa_id.partner_id.name, row_style_)
                    elif col == 15:
                        # raise UserError((o_data[0].exp_close_date))
                        exp_close_date = o_data[0].exp_close_date.strftime("%d %b") if o_data[0].exp_close_date else ''
                        sheet.write(row, col, exp_close_date, row_style)
                    elif col == 16:
                        sheet.write(row, col, '', row_style)

                    col += 1
                row += 1
            sum_start_row = 2
            sum_end_row = row 
            row += 1
            sheet.write(row, 0, '',row_style_border_top_bottom)
            sheet.write(row, 1, '',row_style_border_top_bottom)
            sheet.write(row, 2, '',row_style_border_top_bottom)
            sheet.write(row, 3, '',row_style_border_top_bottom)
            sheet.write(row, 4, '',row_style_border_top_bottom)
            sheet.write(row, 5, '',row_style_border_top_bottom)
            sheet.write(row, 6, '',row_style_border_top_bottom)
            sheet.write(row, 7, '',row_style_border_top_bottom)
            sheet.write(row, 8, '',row_style_border_top_bottom)
            sheet.write(row, 9, f'=SUM(J{sum_start_row}:J{sum_end_row})', row_style_sum)
            sheet.write(row, 10, f'=SUM(K{sum_start_row}:K{sum_end_row})', row_style_sum)
            sheet.write(row, 11, f'=SUM(L{sum_start_row}:L{sum_end_row})', row_style_sum)
            sheet.write(row, 12, '',row_style_border_top_bottom)
            sheet.write(row, 13, '',row_style_border_top_bottom)
            sheet.write(row, 14, '',row_style_border_top_bottom)            
            sheet.write(row, 15, '',row_style_border_top_bottom)
            sheet.write(row, 16, '',row_style_border_top_bottom)
            
             
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Stopper Wise')),
            'target': 'self',
        }


        
