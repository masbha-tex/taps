import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
# from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta
import re
import math
import calendar
from io import StringIO
from io import BytesIO
import xlsxwriter

_logger = logging.getLogger(__name__)


class MrpReportWizard(models.TransientModel):
    _name = 'mrp.report'
    _description = 'MRP Reports'
    _check_company_auto = True
    
    # is_company = fields.Boolean(readonly=False, default=False)
    
    report_type = fields.Selection([('pir', 'PI File'),('pic', 'Closed PI'),('pis', 'PI Summary'),('dpr', 'Invoice'),('dppr', 'Packing Production Report'),('dpcl', 'Production Report (FG)'),('oa_d', 'OA Details'),('invs', 'Invoice Summery')], string='Report Type', required=True, help='Report Type', default='pir')
    
    date_from = fields.Date('Date from', readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', readonly=False, default=lambda self: self._compute_to_date())
    
    month_list = fields.Selection('_get_month_list', 'Month') #, default=lambda self: self._get_month_list()

    file_data = fields.Binary(readonly=True, attachment=False)


    # date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    # date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    # export = fields.Selection([
    #     ('single', 'Single Sheet'),
    #     ('multiple', 'Multiple Sheet')],
    #     string='Export Mode')

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

    def _action_daily_production_email(self, company_id):
        company = self.env['res.company'].search([('id', 'in', (company_id))])
        one_day_ago = datetime.now() - timedelta(days=1)
        for rec in company:
            email_to_list = email_cc_list = []
            subject = (rec.name)+' Daily Production('+(one_day_ago.strftime('%d %b, %Y'))+')'
            body = 'Dear Sir/All, Please Find The Attached Summary of '+(rec.name)+' Daily Production'
            email_from_list = ['odoo@texzipperbd.com',]
            if rec.id == 1:
                email_to_list = ['production@bd.texfasteners.com',]#'asraful.haque@texzipperbd.com',
                email_cc_list = [
                    'deepak.shah@bd.texfasteners.com',
                    'nitish.bassi@texzipperbd.com',
                    'shahid.hossain@texzipperbd.com',
                    'ranjeet.singh@texzipperbd.com',
                    'odoo.support@texzipperbd.com',
                    'abu.sayed@texzipperbd.com',
                    ]
            if rec.id == 3:
                email_to_list = ['packing.button@texzipperbd.com',]#'asraful.haque@texzipperbd.com',
                email_cc_list = [
                    'deepak.shah@bd.texfasteners.com',
                    'nitish.bassi@texzipperbd.com',
                    'shahid.hossain@texzipperbd.com',
                    'kumar.abhishek@texzipperbd.com',
                    'ppc.metaltrims@texzipperbd.com',
                    'odoo.support@texzipperbd.com',
                    'abu.sayed@texzipperbd.com',
                    ]
                
            author_id=0
            report = rec.env.ref('taps_manufacturing.action_daily_production_report', False)
            pdf_content, content_type = report.sudo()._render_qweb_pdf(res_ids=[rec.id], data={"team_id": rec.id})
            attachment = rec.env['ir.attachment'].sudo().create({
                        'name': rec.name+' Daily Production('+(one_day_ago.strftime('%d %b, %Y'))+')'+'.pdf',
                        'type': 'binary',
                        'datas': base64.encodebytes(pdf_content),
                        'mimetype': 'application/pdf',
                        'res_model' : 'operation.details',
            })
            
            email_cc = ','.join(email_cc_list)
            email_from = ','.join(email_from_list)
            email_to = ','.join(email_to_list)
            mail_values = {
                'email_from': email_from,
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': subject,
                'body_html': body,
                'auto_delete': True,
                'email_to': email_to,
                'email_cc': email_cc,
                'attachment_ids' : attachment,
                'reply_to': None,
            }
           
            rec.env['mail.mail'].sudo().create(mail_values).send()
    
    def action_generate_xlsx_report(self):
        if self.report_type == "pir":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            if self.env.company.id == 1:
                return self.pi_xls_template(self, data=data)
            if self.env.company.id == 3:
                return self.pi_mt_xls_template(self, data=data)
        if self.report_type == "oa_d":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            if self.env.company.id == 1:
                return self.oa_details(self, data=data)
            if self.env.company.id == 3:
                return self.oa_details_mt(self, data=data)
        if self.report_type == "pis":
            data = {'date_from': self.date_from,'date_to': self.date_to}
            return self.pis_xls_template(self, data=data)
        if self.report_type == "dpr":
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

    

    def pi_xls_template(self, docids, data=None):
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
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 16, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_top_bottom = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'top': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        row_style_border_left = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'valign': 'vcenter','align': 'center', 'left': True,'bottom': True})
        row_style_border_right = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial',  'valign': 'vcenter','align': 'center', 'right': True})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16,'valign': 'vcenter','align': 'center', 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top','align': 'left', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})

        format_label_5 = workbook.add_format({'font':'Arial', 'font_size': 16, 'valign': 'vcenter','align': 'center', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})
        
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
            # sheet.set_default_row(None)
            sheet.set_default_row(height=None, hide_unused_rows=False)
            sheet.set_row(0, 40)
            
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
            
            sheet.write(0, 0, "CUSTOMER NAME", column_style)
            sheet.write(0, 1, f"PRODUCT: {report_name}", column_style)
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
            sheet.write(0, 14, "PENDING", column_style)
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
            sheet.set_column(3, 3, 14)
            sheet.set_column(4, 4, 12)
            sheet.set_column(5, 5, 8)
            sheet.set_column(6, 6, 12)
            sheet.set_column(7, 7, 0)
            sheet.set_column(8, 8, 20)
            sheet.set_column(9, 9, 35)
            sheet.set_column(10, 10, 11)
            sheet.set_column(11, 11, 11)
            sheet.set_column(12, 12, 15)
            sheet.set_column(13, 13, 15)
            sheet.set_column(14, 14, 15)
            sheet.set_column(14, 20, 12)
            sheet.set_column(15, 15, 0)
            sheet.set_column(17, 22, 0)
            sheet.set_row(0, 28)

            
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
                        customer = " ".join([orders.partner_id.name," ",orders.buyer_name.name," ",payment_term])
                        pi_num = orders.order_ref.pi_number
                        oa_num = int(orders.name.replace('OA',''))
                        if orders.revised_no:
                            oa_num = "\n".join([str(oa_num), str(orders.revised_no).upper()])
                        else:
                            oa_num = str(oa_num)
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

                    


                    
                    if o_data.order_id.cause_of_revision:
                        pr_name = "\n".join([pr_name,"\n",str(orders.revised_no),"\n",o_data.order_id.cause_of_revision])
                    slider = o_data.slidercodesfg
                    finish = o_data.finish #.replace('\n',' ')
                    if isinstance(o_data.shade, str):
                        shade = o_data.shade.replace('[', '').replace(']', ' ')
                    else:
                        o_data.shade
                    if shade:
                        shade_lines = [line for line in shade.split('\n') if line.strip()]
                        shade = '\n'.join(shade_lines)

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
                if _range > 0:
                    _range += 2
                _range += len(report_data)
                
                sheet.merge_range(row_rang, 0, _range, 0, '', merge_format)
                sheet.merge_range(row_rang, 4, _range, 4, '', merge_format)
                sheet.merge_range(row_rang, 5, _range, 5, '', merge_format)
                sheet.merge_range(row_rang, 6, _range, 6, '', merge_format)
                sheet.merge_range(row_rang, 7, _range, 7, '', merge_format)
                sheet.merge_range(row_rang, 8, _range, 8, '', merge_format)

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
                        elif col == 9:
                            sheet.write(row, col, l, format_label_4)
                        elif col == 9 :
                            # sheet.write(row, col, l, format_label_4)
                            if isinstance(l, bool):
                                l = str(l)
                            number_of_newlines = l.count('\n') if isinstance(l, str) else 0
                            if number_of_newlines > 3: 
                                row_height = number_of_newlines * 12
                                sheet.write(row, col, l, format_label_4)
                                sheet.set_row(row, row_height)
                            else :
                                # row_height = 32
                                sheet.write(row, col, l, format_label_4)
                                # sheet.set_row(row, row_height)
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

                sheet.set_row(row, 32)
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
                sheet.write(row, 16, shade_total, row_style)
                sheet.write(row, 17, wire_total, row_style)
                sheet.write(row, 18, slider_total, row_style)
                sheet.write(row, 19, bottom_total, row_style)
                sheet.write(row, 20, top_total, row_style)
                sheet.write(row, 21, '',row_style_border_right)

                # row += 1
                sheet.set_row(row+1, 32)
                row_rang = row + 2
                
                product_range = slider_range = finish_range = shade_range = row_rang - 1
            
            sheet.set_row(row+1, 32)
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
            sheet.set_row(row+1, 32)
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
        closed_orders = self.env['manufacturing.order'].search([('oa_id','!=',None),('state','=','closed'),('closing_date','!=',None),('company_id','=',self.env.company.id)])
        closed_orders = closed_orders.filtered(lambda pr: pr.closing_date.date() >= data.get('date_from') and pr.closing_date.date() <= data.get('date_to'))
                
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 11})
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter','align': 'center', 'bottom': True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})

        red_fill_format = workbook.add_format({'bg_color': '#FF0000', 'align': 'center', 'valign': 'vcenter'})
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

        fg_items = closed_orders.mapped('fg_categ_type')
        fg_items = list(set(fg_items))
        items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
        
        de_items = items.filtered(lambda pr: pr.name not in (fg_items))
        exists_items = items - de_items
        items = exists_items.sorted(key=lambda pr: pr.sequence)
        all_orders = self.env['sale.order.line'].browse(closed_orders.sale_order_line.ids)

        # for item in items:
        #     all_orders = self.env['sale.order.line'].browse(closed_orders.sale_order_line.ids)
            # all_orders = None
            # if item.name == 'Revised PI':
            #     all_orders = self.env['sale.order.line'].browse(rev_orders.sale_order_line.ids)
            # else:
            #     all_orders = self.env['sale.order.line'].browse(closed_orders.sale_order_line.ids)
                # all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type.name == item.name)
            
        # sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.id)
        sale_orders = self.env['sale.order'].browse(all_orders.order_id.ids).sorted(key=lambda pr: pr.closing_date)
        
        # report_name = item.name
        # raise UserError((items))
       
        # sheet = workbook.add_worksheet(('%s' % (report_name)))  
        sheet = workbook.add_worksheet(('Closed PI'))

        
        sheet.set_margins(left=0.2, right=0.3, top=0.2, bottom=0.2)
        sheet.set_footer('Iteam: &A Page: &P of &N Printed at &D &T', {'margin': 0.08, 'align': 'center', 'font_size': 12})
        # sheet.set_footer('Page: &P of &N','Printed at &D &T', {'margin': 0.08, 'align': 'right', 'font_size': 10})
        
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(75)
        sheet.freeze_panes(1, 0)
        sheet.set_paper(9)
                            
        sheet.write(0, 0, "CUSTOMER NAME", column_style)
        sheet.write(0, 1, "PRODUCT", column_style)
        sheet.write(0, 2, "SLIDER CODE", column_style)
        sheet.write(0, 3, "FINISH", column_style)
        sheet.write(0, 4, "PI NO", column_style)
        sheet.write(0, 5, "OA NO", column_style)
        sheet.write(0, 6, "OA DATE", column_style)
        sheet.write(0, 7, "Production DATE", column_style)
        sheet.write(0, 8, "DETAILS", column_style)
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
        sheet.write(0, 22, "CLOSE DATE", column_style)

        sheet.set_column(0, 0, 20)
        sheet.set_column(1, 1, 30)
        sheet.set_column(2, 2, 20)
        sheet.set_column(3, 3, 20)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 20)
        sheet.set_column(8, 8, 40)
        sheet.set_column(9, 9, 40)
        sheet.set_column(22, 22, 20)
        sheet.set_column(14, 21, 0)
        sheet.set_column(7, 7, 0)
        

        
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
            closing_date = ''
            for x,o_data in enumerate(docs):
                # slnumber = slnumber+1 orders.buyer_name.name,
                if x == 0:
                    payment_term = (orders.payment_term_id.name or '')
                    customer = "\n".join([orders.partner_id.name,"\n",payment_term])
                    pi_num = orders.order_ref.pi_number
                    oa_num = orders.name
                    remarks = orders.remarks
                    create_date = orders.create_date.strftime("%d-%m-%Y")
                    if orders.closing_date:
                        closing_date = orders.closing_date.strftime("%d-%m-%Y")
                else:
                    customer = ''
                    pi_num = ''
                    oa_num = ''
                    remarks = ''
                    create_date = ''
                    closing_date = ''
                
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
                    orders.sale_representative.name,
                    closing_date,
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

              # Set row height for the merged cells
            for row_num in range(row_rang, _range + 1):
                sheet.set_row(row_num, 32)  # Adjust the height value as needed
            
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
                        if l:
                            sheet.write(row, col,l, row_style_sum)#'=M{1}-N{1}'.format(row + 1)
                        else:
                            sheet.write(row, col, l, red_fill_format)
                    else:
                        sheet.write(row, col, l, row_style_sum)
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
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','!=','closed'),('company_id','=',self.env.company.id)])
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
                all_orders = all_orders.filtered(lambda pr: pr.product_template_id.fg_categ_type.name == item.name)
            
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
                m_order = self.env['manufacturing.order'].search([('oa_id','=',orders.id),('company_id','=',self.env.company.id)])
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

    
    #packing invoice start here
    def iterate_days(self, year, month):
        _, last_day = calendar.monthrange(year, month)
        # Iterate over all days in the month
        for day in range(1, last_day + 1):
            yield day

    #code for packing_invoice
    def daily_pr_xls_template(self, docids, data=None):
        
        
        start_time = fields.datetime.now()
        month_ = None
        _day = to_day = None
        if data.get('date_from'):
            month_ = int(data.get('date_from').month)#data.get('month_list')
            year = int(data.get('date_from').year)#datetime.today().year
            _day = int(data.get('date_from').day)
        if data.get('date_to'):
            to_day = int(data.get('date_to').day)
            # month_ = int(data.get('date_from').month)#data.get('month_list')
            # year = int(data.get('date_from').year)#datetime.today().year
            

        # raise UserError((int(month_),data.get('date_from').date()))
        # f_date = data.get('date_from')
        # t_date = data.get('date_to')
        first_day_of_m = fields.datetime.now().replace(day = 1).replace(month = int(month_)).replace(year = year)
        # first_day_of_m = full_date
        
        all_outputs = self.env['operation.details'].sudo().search([('next_operation','=','FG Packing'),('company_id','=',self.env.company.id)])
        daily_outputs = all_outputs.filtered(lambda pr: pr.action_date.date() >= first_day_of_m.date() and pr.action_date.date() <= data.get('date_to'))#.sorted(key=lambda pr: pr.sequence)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center', 'bg_color':'#8DB4E2'})
        
        column_merge_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center'})
        
        _row_style = workbook.add_format({'bold': True, 'bg_color':'#FFFF00','font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})
        
        row_style = workbook.add_format({'bold': True, 'bg_color':'#FFFF00','font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True,})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'bg_color': '#FFFF00','left': True, 'top': True, 'right': True, 'bottom': True}) 
        row_style_head = workbook.add_format({'bold': True, 'font_size': 13, 'bg_color': '#8DB4E2','left': True, 'top': True, 'right': True, 'bottom': True}) 
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})#'num_format': '$#,##0'
        
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

        initial_pr = self.env['initial.production'].search([('company_id','=',self.env.company.id),('production_date','>=',data.get('date_from'))])#&gt;
        
        all_closed = self.env['manufacturing.order'].search([('state','=','closed'),('closing_date','!=',False),('company_id','=',self.env.company.id)])
        # for day in self.iterate_days(year, int(month_)):
        for day in self.iterate_days(year, int(month_)):
            if day >= _day and day <= to_day:
                report_name = day
                
                full_date = fields.datetime.now().replace(day = _day).replace(month = int(month_)).replace(year = year)
                first_day_of_m = fields.datetime.now().replace(day = 1).replace(month = int(month_)).replace(year = year) # first day of month
                full_date = full_date.replace(day = day)
                
                datewise_outputs = daily_outputs.filtered(lambda pr: pr.action_date.date() == full_date.date())
                comu_outputs = daily_outputs.filtered(lambda pr: pr.action_date.date() <= full_date.date())
                
                sheet = workbook.add_worksheet(('%s' % (report_name)))
                
                for col_number in range(2):  
                    sheet.write(44, col_number, None, row_style_sum)
                for col_number in range(2):  
                    sheet.write(46, col_number, None, row_style_sum)
                for col_number in range(20): 
                    sheet.write(25, col_number, None, row_style_sum)
                    
                for col_number in range(20): 
                    sheet.write(0, col_number, None, row_style_head)
                for col_number in range(3): 
                    sheet.write(27, col_number, None, row_style_head)

                sheet.set_zoom(85)
                sheet.fit_to_pages(1, 0)
                
                
                sheet.write(0, 0, "DATE :", column_style)
                sheet.write(0, 1, full_date.date().strftime("%d-%b-%Y"), column_style)
                # sheet.write(0, 11, "DATE :", column_style)
                # sheet.merge_range(0, 12, 0, 13, full_date.date().strftime("%d-%b-%Y"), column_style)
                sheet.merge_range(0, 11, 0, 20, 'CLOSED ORDER', column_style)
                sheet.freeze_panes(2, 0)
                if start_time.date() == full_date.date():
                    sheet.activate()
                    
                sheet.write(1, 0, "PRODUCT", column_style)
                sheet.write(1, 1, "PACKING PCS", column_style)
                if self.env.company.id == 3:
                    sheet.write(1, 1, "PACKING GRS", column_style)
                sheet.write(1, 2, "INVOICE USD", column_style)
                sheet.write(1, 3, "PENDING PCS", column_style)
                if self.env.company.id == 3:
                    sheet.write(1, 3, "PENDING GRS", column_style)
                sheet.write(1, 4, "PENDING USD", column_style)
                sheet.write(1, 5, "COMULATIVE PRODUCTION", column_style)
                sheet.write(1, 6, "COMULATIVE INVOICING", column_style)
                sheet.write(1, 7, "TODAY RELEASED", column_style)
                sheet.write(1, 8, "COMULATIVE RELEASED", column_style)
                sheet.write(1, 9, "PENDING OA", column_style)
    
                sheet.set_column(0, 0, 17)
                sheet.set_column(1, 1, 13)
                sheet.set_column(2, 2, 13)
                sheet.set_column(3, 3, 13)
                sheet.set_column(4, 4, 13)
                sheet.set_column(5, 5, 13)
                sheet.set_column(6, 6, 13)
                sheet.set_column(7, 7, 13)
                sheet.set_column(8, 8, 13)
                sheet.set_column(9, 9, 13)
                sheet.set_column(10, 10, 0)
                # sheet.set_column(10, 10, 0)
                sheet.set_column(11, 18, 6)
    
                closed_ids = 0
                # items = datewise_outputs.mapped('fg_categ_type')
                # items = list(set(items))
                running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
    
                daily_closed_oa = None
                if all_closed:
                    daily_closed_oa = all_closed.filtered(lambda pr: pr.closing_date.date() == full_date.date())
                
                if daily_closed_oa:
                    oa_ids = daily_closed_oa.mapped('oa_id')
                    closed_ids = len(oa_ids)
                
                items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
                
                report_data = []
                others_value = 0
                # closed_col = 11
                for item in items:
                    items_comu_outputs = comu_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
                    itemwise_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
                    
                    price = comu_inv = 0
                    comu_pcs = sum(items_comu_outputs.mapped('qty'))
                    comu_inv = sum(pack.qty * pack.price_unit for pack in items_comu_outputs)
                    
                    if comu_pcs > 0 :
                        price = round((comu_inv/comu_pcs),4)
                        # comu_inv = round((comu_pcs*price),2)
                        # c_s_qty = round(sum(items_comu_outputs.mapped('sale_order_line.product_uom_qty')),2)
                        # c_s_value = round(sum(items_comu_outputs.mapped('sale_order_line.price_subtotal')),2)
                        # if c_s_qty>0:
                            
                    invoiced = 0
                    pack_pcs =sum(itemwise_outputs.mapped('qty')) 
                    invoiced = sum(pack.qty * pack.price_unit for pack in itemwise_outputs)
                    
                    
                    if pack_pcs > 0:
                        price = round((invoiced/pack_pcs),4)
                        # invoiced = sum(pack.qty * pack.price_unit for pack in itemwise_outputs)
                        # _s_qty = round(sum(itemwise_outputs.mapped('sale_order_line.product_uom_qty')),2)
                        # _s_value = round(sum(itemwise_outputs.mapped('sale_order_line.price_subtotal')),2)
                        # if _s_qty > 0:
                        
    
                    in_pr = initial_pr.filtered(lambda pr: pr.fg_categ_type == item.name)
                    
                    all_released = self.env['manufacturing.order'].sudo().search([('fg_categ_type','=',item.name),('state','!=','cancel'),('company_id','=',self.env.company.id)])
                    
                    
                    comu_released = all_released.filtered(lambda pr: pr.oa_id.create_date.date() <= full_date.date() and pr.oa_id.create_date.date() >= first_day_of_m.date())#.month == int(month_) and pr.date_order.year == year and pr.date_order.day <= day
    
                    if in_pr:
                        if full_date.date() == in_pr.production_date.date():
                            comu_pcs = in_pr.production_till_date
        
                        cm_pcs = 0
                        cm_rel = sum(comu_released.mapped('product_uom_qty'))
                        if full_date.date() > in_pr.production_date.date():
                            comu_day_outputs = items_comu_outputs.filtered(lambda pr: pr.action_date.date() > in_pr.production_date.date() and pr.action_date.date() <= full_date.date())
                            # cm_day_released = comu_released.filtered(lambda pr: pr.date_order.date() > in_pr.production_date.date())
                            if comu_day_outputs:
                                cm_pcs = sum(comu_day_outputs.mapped('qty'))
                                
                            comu_pcs = in_pr.production_till_date + cm_pcs
    
                    total_qty = comur_value = pending_pcs = pending_usd = 0
                    # pending_usd = 0.0
                    
                    if comu_released:
                        comur_value = round(sum(comu_released.mapped('sale_order_line.price_subtotal')),2)
                        total_qty = sum(comu_released.mapped('sale_order_line.product_uom_qty'))
                        price = round((comur_value / total_qty),4)
                        # pending_pcs = total_qty - comu_pcs
    
                    
                    item_run_ord = running_orders.filtered(lambda pr: pr.fg_categ_type == item.name)
                    # if invoiced == 0:
                    #     invoiced = round((pack_pcs*price),2)
                    # pending_usd = round((pending_pcs*price),2)
                    
                    
                    # not_closed_oa = all_released.sudo().filtered(lambda pr: (pr.date_order.date() <= full_date.date() and pr.closing_date != True))
                                                          
                    # al_closed_oa = all_released.sudo().filtered(lambda pr: (pr.date_order.date() <= full_date.date() and pr.closing_date == True and pr.closing_date.date() > full_date.date()))
    
                    # get_pending = not_closed_oa + al_closed_oa
                    # if get_pendings:
                    #     raise UserError(('yes'))
                                                         
                    query = """ select count(distinct a.oa_id) oa_count,sum(a.product_uom_qty) qty,avg(a.price_unit) price,ARRAY_AGG(distinct a.oa_id) oa_ids  from manufacturing_order as a inner join sale_order as s on a.oa_id=s.id and a.company_id = s.company_id where a.company_id = %s and a.state not in ('cancel') and date(s.create_date) <= %s and (a.closing_date is null or date(a.closing_date) > %s) and a.fg_categ_type = %s """
                    self.env.cr.execute(query, (self.env.company.id,full_date.date(),full_date.date(),item.name))
                    get_pending = self.env.cr.fetchone()
    
                    # _top = self.env['operation.details'].search([('sale_line_of_top','=',o_data.id),('company_id','=',self.env.company.id)])
                    
                    # pending_oa = all_released.filtered(lambda pr: (pr.date_order.date() <= full_date.date() and  (pr.closing_date != True or (getattr(pr.closing_date, 'date', lambda: None)() == True and pr.closing_date.date() > full_date.date()) ) ))
                    
                    pending_ids = 0
                    
                    if len(get_pending) > 1: #get_pending:#
                        # raise UserError((get_pending[0],get_pending[1],get_pending[3]))
                        # oa_ids = pending_oa.mapped('oa_id')
                        pending_oa_ids = None
                        pending_oa_ids = get_pending[3]
                        if pending_oa_ids:
                            # pending_oa_ids = set(get_pending.mapped('oa_id.id')) #set(get_pending[3])
                            # raise UserError((pending_oa_ids))
                            pending_oa_ids = ','.join([str(i) for i in sorted(pending_oa_ids)])
                            pending_oa_ids = [int(i) for i in sorted(pending_oa_ids.split(','))]
                        # raise UserError((pending_oa_ids))
                            pending_ids = get_pending[0]
                            qty = get_pending[1]#sum(get_pending.mapped('product_uom_qty'))#
                            # val = round(sum(get_pending.mapped('sale_order_line.price_subtotal')),2)
                            # if qty > 0:
                            price = get_pending[2]#round(val/qty,2)
                            
                            pending_pcs = qty
    
                            pending_orders = self.env['manufacturing.order'].search([('oa_id','in',(pending_oa_ids)),('company_id','=',self.env.company.id)])
                            if pending_orders:
                                vl = round(sum(pending_orders.mapped('sale_order_line.price_subtotal')),2)
                                _qty = sum(pending_orders.mapped('sale_order_line.product_uom_qty'))
                                price = round((vl / _qty),4)
                                
                            pending_usd = round((pending_pcs * price),2)
    
                            if item.name == 'Others':
                                all_top_outputs = self.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('company_id','=',self.env.company.id),('fg_categ_type','=',item.name),('oa_id.id','in',pending_oa_ids),('product_template_id.name','=','TOP')])
                                if all_top_outputs:
                                    pending_pcs += sum(all_top_outputs.mapped('qty'))
                                    qty = pending_pcs
                                    # raise UserError((qty))
                                # _top_outputs = all_top_outputs.sudo().filtered(lambda pr: (pr.action_date.date() <= full_date.date() and  pr.fg_categ_type == item.name and pr.oa_id.id in pending_oa_ids))
                            
                            _outputs = all_outputs.sudo().filtered(lambda pr: (pr.action_date.date() <= full_date.date() and  pr.fg_categ_type == item.name and pr.oa_id.id in pending_oa_ids))
                            if _outputs:
                                doneqty = sum(_outputs.mapped('qty'))
                                pending_pcs = qty - doneqty
                                pending_usd = round((pending_pcs * price),2)
                    
                    # if start_time.date() == full_date.date():
                    #     # raise UserError((start_time.date(),full_date.date()))
                    #     pending_pcs = sum(item_run_ord.mapped('balance_qty'))
                    #     oa_ids = item_run_ord.mapped('oa_id')
                    #     pending_ids = len(oa_ids)
                    #     # pending_ids = sum(item_run_ord.mapped('balance_qty'))
                        
                    #     vl = round(sum(item_run_ord.mapped('sale_order_line.price_subtotal')),2)
                    #     _qty = sum(item_run_ord.mapped('sale_order_line.product_uom_qty'))
                    #     if _qty > 0 and pending_pcs > 0:
                    #         price = round((vl / _qty),4)
                    #         pending_usd = round((pending_pcs*price),2)
    
    
    
                    
                    today_released = all_released.filtered(lambda pr: pr.oa_id.create_date.date() == full_date.date())
                    tr_value = round(sum(today_released.mapped('sale_order_line.price_subtotal')),2)
                    if in_pr:
                        if full_date.date() == in_pr.production_date.date():
                            comu_inv = in_pr.invoice_till_date
                            comur_value = in_pr.released_till_date
                            
                        if full_date.date() > in_pr.production_date.date():
                            cmr_val = 0
                            comu_released_ = all_released.filtered(lambda pr: pr.oa_id.create_date.date() <= full_date.date() and pr.oa_id.create_date.date() > in_pr.production_date.date())
                            if comu_released_:
                                cmr_val = round(sum(comu_released_.mapped('sale_order_line.price_subtotal')),2)
                                # sum(comu_released.mapped('product_uom_qty'))
                            cm_inv = price * cm_pcs
                            comu_inv = in_pr.invoice_till_date + cm_inv
                            comur_value = in_pr.released_till_date + cmr_val
                    
                    order_data = []
                    
                    invoiced = round(invoiced,0)
                    # if pending_usd == None:
                    #     raise UserError((pending_usd))
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
                            pending_pcs,
                            pending_usd,
                        if comu_pcs == 0:
                            comu_pcs = None
                        if pending_ids == 0:
                            pending_ids = None
        
                        if invoiced == 0:
                            invoiced = None
                        if comu_inv == 0:
                            comu_inv = None
                        if tr_value == 0:
                            tr_value = None    
                        if comur_value == 0:
                            comur_value = None
                    if item.name == 'Others':
                        others_value = invoiced
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
                
                row = 2
                type_exists = []
                closed_col = 11
                for line in report_data:
                    item_type = line[0].replace('CE','').replace('OE','')
                    if (((line[1] or 0) + (line[3] or 0)) > 0) and (item_type not in type_exists):
                        closed_row = 2
                        itemwise_closed = daily_closed_oa.filtered(lambda pr: pr.fg_categ_type.replace('CE','').replace('OE','') == item_type)
                        c_col = closed_col
                        if line[0] == 'M#4 CE':
                            sheet.merge_range(1, closed_col, 1, closed_col+1, item_type, column_style)
                            closed_col += 2
                        else:
                            sheet.write(1, closed_col, item_type, column_style)
                            closed_col += 1
                        if itemwise_closed:
                            closed_oa_list = list(set(itemwise_closed.mapped('oa_id.name')))
                            if closed_oa_list:
                                for index, oa in enumerate(closed_oa_list):
                                    if closed_row == 24:
                                        closed_row = 1
                                        c_col += 1
                                    sheet.write(closed_row, c_col, int(oa.replace('OA','0')), format_label_1)
                                    closed_row += 1
                        
                        if closed_row < 24 and c_col == 11:
                            for i in range(closed_row,25):
                                sheet.write(closed_row, c_col, '', format_label_1)
                                if closed_row == 24 and line[0] == 'M#4 CE':
                                    closed_row = 1
                                    c_col += 1
                                closed_row += 1
                            # for i in range(24)[:closed_row]:
                            #     sheet.write(closed_row, c_col, '', format_label_1)
                            #     closed_row += 1
                        if closed_row < 24 and c_col != 11:
                            for i in range(closed_row, 25):
                                sheet.write(closed_row, c_col, '', format_label_1)
                                closed_row += 1
                    
                    if item_type not in type_exists:
                        type_exists.append(item_type)
                    col = 0
                    for l in line:
                        if col in (2,4,6,7,8):
                            sheet.write(row, col, l, format_label_2)
                        else:
                            sheet.write(row, col, l, format_label_1)
                        col += 1
                    row += 1
                # raise UserError((type_exists))
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
                
                others_item_config = self.env['others.item.config'].sudo().search([('company_id','=',self.env.company.id)])
                row += 2
                
                sheet.write(row, 0, "DATE :", column_style)
                sheet.write(row, 1, full_date.date().strftime("%d-%b-%Y"), column_style)
                row += 1
                sheet.write(row, 0, 'OTHERS ITEM NAME', column_style)
                sheet.write(row, 1, 'PACKED PCS', column_style)
                sheet.write(row, 2, 'UNIT', column_style)
                row += 1
                others_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == 'Others')
                for ot in others_item_config:
                    sheet.write(row, 0, ot.others_item, format_label_1)
                    others_itemwise = others_outputs.filtered(lambda pr: pr.product_template_id.id == ot.product_tmpl_id.id)
                    if others_itemwise:
                        pac_pcs = sum(others_itemwise.mapped('qty'))
                        sheet.write(row, 1, pac_pcs, format_label_1)
                    else:
                        sheet.write(row, 1, '', format_label_1)
                    sheet.write(row, 2, ot.unit, format_label_1)
                    row += 1
                sheet.write(row, 0, 'TOTAL', format_label_1)
                sheet.write(row, 1, '=SUM(B{0}:B{1})'.format(29, 44), format_label_1)
                sheet.write(row+2, 0, 'TOTAL PRICE', format_label_2)
                sheet.write(row+2, 1, others_value, format_label_1)

            # if start_time.day == day and start_time.month == int(month_):
            #     sheet.Activate()
        # raise UserError(())
        # workbook.active =  start_time.day  
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        # raise UserError((end_time))
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(
                self._name, self.id, ('Invoice')),
            'target': 'self',
        }
    #FG Invoice start Here 
    
    def iterate_days(self, year, month):
        # Get the number of days in the given month
        _, last_day = calendar.monthrange(year, month)
    
        # Iterate over all days in the month
        for day in range(1, last_day + 1):
            yield day

    def daily_closed_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        month_ = _day = to_day = None
        if data.get('date_from'):
            month_ = int(data.get('date_from').month)#data.get('month_list')
            year = int(data.get('date_from').year)#datetime.today().year
            _day = int(data.get('date_from').day)
            
        if data.get('date_to'):
            to_day = int(data.get('date_to').day)

        # raise UserError((int(month_),data.get('date_from').date()))
        # f_date = data.get('date_from')
        # t_date = data.get('date_to')
        
        all_outputs = self.env['operation.details'].sudo().search([('next_operation','=','FG Packing'),('company_id','=',self.env.company.id)])
        daily_outputs = all_outputs.filtered(lambda pr: pr.action_date.date() >= data.get('date_from') and pr.action_date.date() <= data.get('date_to'))#.sorted(key=lambda pr: pr.sequence)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        
        column_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center', 'bg_color':'#8DB4E2'})
        
        column_merge_style = workbook.add_format({'bold': True, 'font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'valign': 'vcenter', 'align': 'center'})
        row_style_head = workbook.add_format({'bold': True, 'font_size': 13,'align': 'center','valign': 'vcenter', 'bg_color': '#8DB4E2','left': True, 'top': True, 'right': True, 'bottom': True}) 
        
        _row_style = workbook.add_format({'bold': True, 'bg_color':'#FFFF00','font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True,'valign': 'vcenter', 'bottom': True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})
        row_style_sum = workbook.add_format({'bold': True, 'font_size': 13, 'bg_color': '#FFFF00','left': True, 'top': True, 'right': True, 'bottom': True}) 
        
        row_style = workbook.add_format({'bold': True, 'bg_color':'#FFFF00','font_size': 11, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'align': 'center','valign': 'vcenter', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True, 'num_format': '_("$"* #,##0_);_("$"* \(#,##0\);_("$"* "-"_);_(@_)'})#'num_format': '$#,##0'
        
        
        merge_format = workbook.add_format({'align': 'top'})
        merge_format_ = workbook.add_format({'align': 'bottom'})

        initial_pr = self.env['initial.production'].search([('company_id','=',self.env.company.id),('production_date','>=',data.get('date_from'))])#&gt;
        
        all_closed = self.env['manufacturing.order'].search([('state','=','closed'),('closing_date','!=',False),('company_id','=',self.env.company.id)])
        
        for day in self.iterate_days(year, int(month_)):
            if day >= _day and day <= to_day:
                report_name = day
                
                full_date = fields.datetime.now().replace(day = _day).replace(month = int(month_)).replace(year = year)
                first_day_of_m = full_date # first day of month
                full_date = full_date.replace(day = day)
                
                datewise_outputs = daily_outputs.filtered(lambda pr: pr.action_date.date() == full_date.date())
                            
                sheet = workbook.add_worksheet(('%s' % (report_name)))
                for col_number in range(16):  
                    sheet.write(25, col_number, None, row_style_sum)
                for col_number in range(2):  
                    sheet.write(44, col_number, None, row_style_sum)
                for col_number in range(16):  
                    sheet.write(0, col_number, None, row_style_head)
                for col_number in range(3):  
                    sheet.write(27, col_number, None, row_style_head)
               
                
                
                sheet.write(0, 0, "DATE :", column_style)
                sheet.write(0, 1, full_date.date().strftime("%d-%b-%Y"), column_style)
                # sheet.write(0, 11, "DATE :", column_style)
                # sheet.merge_range(0, 12, 0, 13, full_date.date().strftime("%d-%b-%Y"), column_style)
                sheet.merge_range(0, 2, 0, 15, 'CLOSED ORDER', row_style_head)
                sheet.freeze_panes(2, 0)
                if start_time.date() == full_date.date():
                    sheet.activate()
                    
                sheet.write(1, 0, "PRODUCT", column_style)
                sheet.write(1, 1, "PACKING PCS", column_style)
    
                sheet.set_column(0, 0, 16)
                sheet.set_column(1, 1, 12)
                sheet.set_column(2, 16, 7)
                sheet.set_column(7, 8, 0)
                sheet.set_column(14,14, 0)
                sheet.set_column(6,6, 0)

                sheet.set_row(1, 30)
    
                closed_ids = 0
                # items = datewise_outputs.mapped('fg_categ_type')
                # items = list(set(items))
                running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
    
                daily_closed_oa = None
                if all_closed:
                    daily_closed_oa = all_closed.filtered(lambda pr: pr.closing_date.date() == full_date.date())
                
                if daily_closed_oa:
                    oa_ids = daily_closed_oa.mapped('oa_id')
                    closed_ids = len(oa_ids)
                
                items = self.env['fg.category'].search([('active','=',True),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
                
                report_data = []
                others_value = 0
                # closed_col = 11
                for item in items:
                    itemwise_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
                    price = comu_inv = 0
                    
                    pack_pcs = sum(itemwise_outputs.mapped('qty'))
                    if pack_pcs > 0:
                        _s_qty = round(sum(itemwise_outputs.mapped('sale_order_line.product_uom_qty')),2)
                        _s_value = round(sum(itemwise_outputs.mapped('sale_order_line.price_subtotal')),2)
                        if _s_qty > 0:
                            price = round((_s_value/_s_qty),4)
                    
                    
                    invoiced = round((pack_pcs*price),2)
                    
                    pending_ids = 0
                    #today_released = all_released.filtered(lambda pr: pr.oa_id.create_date.date() == full_date.date())    
                    
                    order_data = []
                    
                    invoiced = round(invoiced,0)
                    
                    if start_time.date() < full_date.date():
                        invoiced = pack_pcs = None
    
                    else:
                        if pack_pcs == 0:
                            pack_pcs = None
        
                        if invoiced == 0:
                            invoiced = None
                    if item.name == 'Others':
                        others_value = invoiced
                    order_data = [
                        item.name,
                        pack_pcs
                        ]
                    report_data.append(order_data)
                
                row = 2
    
                type_exists = []
                closed_col = 2
                for line in report_data:
                    item_type = line[0].replace('CE','').replace('OE','')
                    if item_type not in type_exists:#(line[1] or 0) > 0
                        closed_row = 2
                        itemwise_closed = daily_closed_oa.filtered(lambda pr: pr.fg_categ_type.replace('CE','').replace('OE','') == item_type)
                        c_col = closed_col
                        if line[0] == 'M#4 CE':
                            sheet.merge_range(1, closed_col, 1, closed_col+1, item_type, column_style)
                            closed_col += 2
                        else:
                            sheet.write(1, closed_col, item_type, column_style)
                            closed_col += 1
                        if itemwise_closed:
                            closed_oa_list = list(set(itemwise_closed.mapped('oa_id.name')))
                            if closed_oa_list:
                                for index, oa in enumerate(closed_oa_list):
                                    if closed_row == 24:
                                        closed_row = 1
                                        c_col += 1
                                    sheet.write(closed_row, c_col, int(oa.replace('OA','0')), format_label_1)
                                    closed_row += 1
                        
                        if closed_row < 24 and c_col == 11:
                            for i in range(closed_row,25):
                                sheet.write(closed_row, c_col, '', format_label_1)
                                if closed_row == 24 and line[0] == 'M#4 CE':
                                    closed_row = 1
                                    c_col += 1
                                closed_row += 1
                            # for i in range(24)[:closed_row]:
                            #     sheet.write(closed_row, c_col, '', format_label_1)
                            #     closed_row += 1
                        if closed_row < 24 and c_col != 11:
                            for i in range(closed_row, 25):
                                sheet.write(closed_row, c_col, '', format_label_1)
                                closed_row += 1
                    if item_type not in type_exists:
                        type_exists.append(item_type)    
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
                sheet.write(row, 3, '', format_label_3)
                sheet.write(row, 4, '', format_label_3)
                sheet.write(row, 5, '', format_label_3)
                sheet.write(row, 6, '', format_label_3)
                sheet.write(row, 7, '', format_label_3)
                sheet.write(row, 8, '', format_label_3)
                sheet.write(row, 9, '', format_label_3)
                row += 1    
                sheet.write(row, 0, 'TOTAL', row_style)
                sheet.write(row, 1, '=SUM(B{0}:B{1})'.format(1, row-1), row_style)
    
                
                others_item_config = self.env['others.item.config'].sudo().search([('company_id','=',self.env.company.id)])
                row += 2
                
                sheet.write(row, 0, "DATE :", column_style)
                sheet.write(row, 1, full_date.date().strftime("%d-%b-%Y"), column_style)
                row += 1
                sheet.write(row, 0, 'OTHERS ITEM NAME', column_style)
                sheet.write(row, 1, 'PACKED PCS', column_style)
                sheet.write(row, 2, 'UNIT', column_style)
                row += 1
                others_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == 'Others')
                for ot in others_item_config:
                    sheet.write(row, 0, ot.others_item, format_label_1)
                    others_itemwise = others_outputs.filtered(lambda pr: pr.product_template_id.id == ot.product_tmpl_id.id)
                    if others_itemwise:
                        pac_pcs = sum(others_itemwise.mapped('qty'))
                        sheet.write(row, 1, pac_pcs, format_label_1)
                    else:
                        sheet.write(row, 1, '', format_label_1)
                    sheet.write(row, 2, ot.unit, format_label_1)
                    row += 1
                sheet.write(row, 0, 'TOTAL', row_style_sum)
                sheet.write(row, 1, '=SUM(B{0}:B{1})'.format(29, 43), row_style_sum)
                # sheet.write(row+2, 0, 'TOTAL PRICE', format_label_2)
                # sheet.write(row+2, 1, others_value, format_label_1)

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
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Production Report (FG)')),
            'target': 'self',
        }

    #fg invoice  code end here 
    
    #daily production report start here
    def packing_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        
        all_outputs = self.env['operation.details'].search([('next_operation','=','FG Packing'),('company_id','=',self.env.company.id)])
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

                    if i.slidercodesfg:
                        if i.slidercodesfg != 'TBA':
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
        
    #Button_pi
    def pi_mt_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        # domain = []
        # if data.get('date_from'):
        #     domain.append(('date_from', '=', data.get('date_from'))) 
        docs = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('balance_qty','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet("PI PENDING MT EXCEL")
        column_style = workbook.add_format({'bold': True, 'font_size': 12})
        
        row_style = workbook.add_format({'font_size': 12, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap':False})

        sheet.write(0, 0, "OA", column_style)
        sheet.write(0, 1, "OA DATE", column_style)
        sheet.write(0, 2, "CUSTOMER ", column_style)
        sheet.write(0, 3, "BUYER", column_style)
        sheet.write(0, 4, "LOGO", column_style)
        sheet.write(0, 5, "SIZE", column_style)
        #sheet.write(0, 6, "MATERIAL( ALLOY / BRASS)", column_style)
        sheet.write(0, 6, "FINISH", column_style)
        sheet.write(0, 7, "B PART", column_style)
        sheet.write(0, 8, "QTY", column_style)
        sheet.write(0, 9, "READY", column_style)
        sheet.write(0, 10, "PENDING", column_style)
        col = 0
        row = 1

        #docs = self.env['sale.order.line'].browse(running_orders.sale_order_line.ids).sorted(key=lambda pr: pr.order_id and pr.id)

        
        for o_data in docs:
            col = 0
            for l in range(17):
                if col == 0:
                    sheet.write(row, col, o_data.oa_id.name, row_style)
                #elif col == 1:
                    #sheet.write(row, col, o_data.order_id.expected_date.strftime("%d/%m/%Y"), row_style)
                elif col == 1:
                    sheet.write(row, col, o_data.oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                #elif col == 3:
                    #sheet.write(row, col, o_data.order_id.order_ref.pi_number, row_style)
                elif col == 2:
                    sheet.write(row, col, o_data.oa_id.partner_id.name, row_style)
                elif col == 3:
                    sheet.write(row, col, o_data.oa_id.buyer_name.name, row_style)
                #elif col == 4:
                    #sheet.write(row, col, '', row_style)
                elif col == 4:
                    if o_data.logo:
                        sheet.write(row, col, o_data.logo, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 5:
                    sheet.write(row, col, o_data.sizemm, row_style)
                elif col == 6:
                    if o_data.finish:
                        sheet.write(row, col, o_data.finish, row_style)
                    else:
                        sheet.write(row, col,'', row_style)
                    sheet.write(row, col, o_data.product_template_id.name, row_style)
                elif col == 7:
                    if o_data.b_part:
                        sheet.write(row, col, o_data.b_part, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 8:
                    sheet.write(row, col, o_data.product_uom_qty, row_style)
                elif col == 9:
                    sheet.write(row, col, o_data.done_qty , row_style)
                elif col == 10:
                    sheet.write(row, col, o_data.balance_qty , row_style)

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
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('MT PI File')),
            'target': 'self',
        }


       # OA Details 
    def oa_details(self, docids, data=None):
        start_time = fields.datetime.now()
        # domain = []
        # if data.get('date_from'):
        #     domain.append(('date_from', '=', data.get('date_from'))) 
        docs = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('balance_qty','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)]).sorted(key=lambda pr: pr.oa_id and pr.sale_order_line)
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})

        sheet = workbook.add_worksheet("PI PENDING MT EXCEL")
        column_style = workbook.add_format({'bold': True, 'font_size': 12})
        
        row_style = workbook.add_format({'font_size': 12, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True, 'align': 'center', 'valign': 'vcenter', 'text_wrap':False})

        sheet.write(0, 0, "OA", column_style)
        sheet.write(0, 1, "OA DATE", column_style)
        sheet.write(0, 2, "CUSTOMER ", column_style)
        sheet.write(0, 3, "BUYER", column_style)
        sheet.write(0, 4, "LOGO", column_style)
        sheet.write(0, 5, "SIZE", column_style)
        #sheet.write(0, 6, "MATERIAL( ALLOY / BRASS)", column_style)
        sheet.write(0, 6, "FINISH", column_style)
        sheet.write(0, 7, "B PART", column_style)
        sheet.write(0, 8, "QTY", column_style)
        sheet.write(0, 9, "READY", column_style)
        sheet.write(0, 10, "PENDING", column_style)
        col = 0
        row = 1

        #docs = self.env['sale.order.line'].browse(running_orders.sale_order_line.ids).sorted(key=lambda pr: pr.order_id and pr.id)

        
        for o_data in docs:
            col = 0
            for l in range(17):
                if col == 0:
                    sheet.write(row, col, o_data.oa_id.name, row_style)
                #elif col == 1:
                    #sheet.write(row, col, o_data.order_id.expected_date.strftime("%d/%m/%Y"), row_style)
                elif col == 1:
                    sheet.write(row, col, o_data.oa_id.create_date.strftime("%d/%m/%Y"), row_style)
                #elif col == 3:
                    #sheet.write(row, col, o_data.order_id.order_ref.pi_number, row_style)
                elif col == 2:
                    sheet.write(row, col, o_data.oa_id.partner_id.name, row_style)
                elif col == 3:
                    sheet.write(row, col, o_data.oa_id.buyer_name.name, row_style)
                #elif col == 4:
                    #sheet.write(row, col, '', row_style)
                elif col == 4:
                    if o_data.logo:
                        sheet.write(row, col, o_data.logo, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 5:
                    sheet.write(row, col, o_data.sizemm, row_style)
                elif col == 6:
                    if o_data.finish:
                        sheet.write(row, col, o_data.finish, row_style)
                    else:
                        sheet.write(row, col,'', row_style)
                    sheet.write(row, col, o_data.product_template_id.name, row_style)
                elif col == 7:
                    if o_data.b_part:
                        sheet.write(row, col, o_data.b_part, row_style)
                    else:
                        sheet.write(row, col, '', row_style)
                elif col == 8:
                    sheet.write(row, col, o_data.product_uom_qty, row_style)
                elif col == 9:
                    sheet.write(row, col, o_data.done_qty , row_style)
                elif col == 10:
                    sheet.write(row, col, o_data.balance_qty , row_style)

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
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('MT PI File')),
            'target': 'self',
        }
















class ProductionReportPDF(models.AbstractModel):
    _name = 'report.taps_manufacturing.view_email_template_daily_production'
    _description = 'Production Report Template'     

    def _get_report_values(self, docids, data=None):
        # raise UserError((docids[0]))
        com_id = int(docids[0])
        start_time = fields.datetime.now()
        one_day_ago = start_time - timedelta(days=1)
        report_date = one_day_ago.strftime("%d-%b-%Y")
        month_ = _day = to_day = None
        
        month_ = int(one_day_ago.month)
        year = int(one_day_ago.year)
        _day = int(one_day_ago.day)
        to_day = int(one_day_ago.day)
        
        first_day_of_m = fields.datetime.now().replace(year = year).replace(month = int(month_)).replace(day = 1)
        
        all_outputs = self.env['operation.details'].sudo().search([('next_operation','=','FG Packing'),('company_id.id','=',com_id)])
        daily_outputs = all_outputs.filtered(lambda pr: pr.action_date.date() >= first_day_of_m.date() and pr.action_date.date() <= one_day_ago.date())#.sorted(key=lambda pr: pr.sequence)
        

        initial_pr = self.env['initial.production'].search([('company_id.id','=',com_id),('production_date','>=',one_day_ago.date())])#&gt;
        
        all_closed = self.env['manufacturing.order'].search([('state','=','closed'),('closing_date','!=',False),('company_id.id','=',com_id)])
        day = _day
        
        report_name = day
        full_date = fields.datetime.now().replace(year = year).replace(month = int(month_)).replace(day = _day)
         # first day of month
        full_date = full_date.replace(day = day)
        
        datewise_outputs = daily_outputs.filtered(lambda pr: pr.action_date.date() == full_date.date())
        comu_outputs = daily_outputs.filtered(lambda pr: pr.action_date.date() <= full_date.date())
        

        closed_ids = 0
        
        running_orders = self.env['manufacturing.order'].search([('oa_total_balance','>',0),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id.id','=',com_id)])

        daily_closed_oa = None
        if all_closed:
            daily_closed_oa = all_closed.filtered(lambda pr: pr.closing_date.date() == full_date.date())
        
        if daily_closed_oa:
            oa_ids = daily_closed_oa.mapped('oa_id')
            closed_ids = len(oa_ids)
        
        items = self.env['fg.category'].search([('active','=',True),('company_id.id','=',com_id),('name','!=','Revised PI')]).sorted(key=lambda pr: pr.sequence)
        
        report_data = []
        others_value = 0
        # closed_col = 11
        for item in items:
            items_comu_outputs = comu_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
            itemwise_outputs = datewise_outputs.filtered(lambda pr: pr.fg_categ_type == item.name)
            
            price = comu_inv = 0
            comu_pcs = sum(items_comu_outputs.mapped('qty'))
            comu_inv = sum(pack.qty * pack.price_unit for pack in items_comu_outputs)
            if comu_pcs > 0 :
                price = round((comu_inv/comu_pcs),4)
                # c_s_qty = round(sum(items_comu_outputs.mapped('sale_order_line.product_uom_qty')),2)
                # c_s_value = round(sum(items_comu_outputs.mapped('sale_order_line.price_subtotal')),2)
                # if c_s_qty>0:
                #     price = round((c_s_value/c_s_qty),4)
                #     comu_inv = round((comu_pcs*price),2)
            invoiced = 0
            pack_pcs = sum(itemwise_outputs.mapped('qty'))
            
            if pack_pcs > 0:
                invoiced = sum(pack.qty * pack.price_unit for pack in itemwise_outputs)
                price = round((invoiced/pack_pcs),4)

            in_pr = initial_pr.filtered(lambda pr: pr.fg_categ_type == item.name)
            
            all_released = self.env['manufacturing.order'].sudo().search([('fg_categ_type','=',item.name),('state','!=','cancel'),('company_id.id','=',com_id)])
            
            
            comu_released = all_released.filtered(lambda pr: pr.oa_id.create_date.date() <= full_date.date() and pr.oa_id.create_date.date() >= first_day_of_m.date())

            if in_pr:
                if full_date.date() == in_pr.production_date.date():
                    comu_pcs = in_pr.production_till_date

                cm_pcs = 0
                cm_rel = sum(comu_released.mapped('product_uom_qty'))
                if full_date.date() > in_pr.production_date.date():
                    comu_day_outputs = items_comu_outputs.filtered(lambda pr: pr.action_date.date() > in_pr.production_date.date() and pr.action_date.date() <= full_date.date())
                    if comu_day_outputs:
                        cm_pcs = sum(comu_day_outputs.mapped('qty'))
                        
                    comu_pcs = in_pr.production_till_date + cm_pcs

            total_qty = comur_value = pending_pcs = pending_usd = 0
            
            if comu_released:
                comur_value = round(sum(comu_released.mapped('sale_order_line.price_subtotal')),2)
                total_qty = sum(comu_released.mapped('sale_order_line.product_uom_qty'))
                price = round((comur_value / total_qty),4)
                # pending_pcs = total_qty - comu_pcs

            
            item_run_ord = running_orders.filtered(lambda pr: pr.fg_categ_type == item.name)
                                                 
            query = """ select count(distinct a.oa_id) oa_count,sum(a.product_uom_qty) qty,avg(a.price_unit) price,ARRAY_AGG(distinct a.oa_id) oa_ids  from manufacturing_order as a inner join sale_order as s on a.oa_id=s.id and a.company_id = s.company_id where a.company_id = %s and a.state not in ('cancel') and date(s.create_date) <= %s and (a.closing_date is null or date(a.closing_date) > %s) and a.fg_categ_type = %s """
            self.env.cr.execute(query, (com_id,full_date.date(),full_date.date(),item.name))
            get_pending = self.env.cr.fetchone()
            
            pending_ids = 0
            
            if len(get_pending) > 1:
                pending_oa_ids = None
                pending_oa_ids = get_pending[3]
                if pending_oa_ids:
                    pending_oa_ids = ','.join([str(i) for i in sorted(pending_oa_ids)])
                    pending_oa_ids = [int(i) for i in sorted(pending_oa_ids.split(','))]
                    pending_ids = get_pending[0]
                    qty = get_pending[1]
                    price = get_pending[2]
                    
                    pending_pcs = qty

                    pending_orders = self.env['manufacturing.order'].search([('oa_id','in',(pending_oa_ids)),('company_id.id','=',com_id)])
                    if pending_orders:
                        vl = round(sum(pending_orders.mapped('sale_order_line.price_subtotal')),2)
                        _qty = sum(pending_orders.mapped('sale_order_line.product_uom_qty'))
                        price = round((vl / _qty),4)
                        
                    pending_usd = round((pending_pcs * price),2)

                    if item.name == 'Others':
                        all_top_outputs = self.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('company_id.id','=',com_id),('fg_categ_type','=',item.name),('oa_id.id','in',pending_oa_ids),('product_template_id.name','=','TOP')])
                        if all_top_outputs:
                            pending_pcs += sum(all_top_outputs.mapped('qty'))
                            qty = pending_pcs
                            
                    _outputs = all_outputs.sudo().filtered(lambda pr: (pr.action_date.date() <= full_date.date() and  pr.fg_categ_type == item.name and pr.oa_id.id in pending_oa_ids))
                    if _outputs:
                        doneqty = sum(_outputs.mapped('qty'))
                        if com_id == 3:
                            pending_pcs = round((qty - doneqty),2)
                        else:
                            pending_pcs = qty - doneqty
                        pending_usd = round((pending_pcs * price),2)
            
            
            today_released = all_released.filtered(lambda pr: pr.oa_id.create_date.date() == full_date.date())
            tr_value = round(sum(today_released.mapped('sale_order_line.price_subtotal')),2)
            if in_pr:
                if full_date.date() == in_pr.production_date.date():
                    comu_inv = in_pr.invoice_till_date
                    comur_value = in_pr.released_till_date
                    
                if full_date.date() > in_pr.production_date.date():
                    cmr_val = 0
                    comu_released_ = all_released.filtered(lambda pr: pr.oa_id.create_date.date() <= full_date.date() and pr.oa_id.create_date.date() > in_pr.production_date.date())
                    if comu_released_:
                        cmr_val = round(sum(comu_released_.mapped('sale_order_line.price_subtotal')),2)
                        # sum(comu_released.mapped('product_uom_qty'))
                    cm_inv = price * cm_pcs
                    comu_inv = in_pr.invoice_till_date + cm_inv
                    comur_value = in_pr.released_till_date + cmr_val
            
            order_data = []
            
            invoiced = round(invoiced,0)
            # if pending_usd == None:
            #     raise UserError((pending_usd))
            pending_usd = round(pending_usd,0)
            comu_inv = round(comu_inv,0)
            tr_value = round(tr_value,0)
            comur_value = round(comur_value,0)

            
            if item.name == 'Others':
                others_value = invoiced
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
            
        return {
            'datas': report_data,
            'closedids':closed_ids,
            'report_date':report_date,
            'company': com_id,
            }
 