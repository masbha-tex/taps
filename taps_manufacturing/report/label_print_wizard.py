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


class LabelPrintingWizard(models.TransientModel):
    _name = 'label.print'
    _description = 'Label Printing'
    _check_company_auto = True
    
    # is_company = fields.Boolean(readonly=False, default=False)
    
    report_type = fields.Selection([('pplg', 'Production Packing Label (General)'),('fgcl', 'FG Carton Label'),('pplo', 'Production Packing Label (Others)')], string='Report Type', required=True, help='Report Type', default='pplg')
    
    # company_name = fields.Char('Company Name', readonly=False, default='TEX ZIPPERS (BD) LIMITED')     
    # company_address = fields.Char('Company Address', readonly=False, default='Plot # 180, 264 & 273 Adamjee Export Processing Zone, Adamjee Nagar, Shiddhirgonj, Narayangonj, Bangladesh')  

    table_name = fields.Selection([('a', 'Table A'),('b', 'Table B')], string='Table', required=True, help='Table', default='a')
    Country_name = fields.Selection([('bangladesh', 'Bangladesh'),('vietnam', 'Vietnam'),('pakistan', 'Pakistan')], string='Country', required=True, help='Country', default='bangladesh')

    #oa_number = fields.Integer("OA", required=True)
    #oa_number = fields.Many2one(filter(lambda x: x.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)]), sale.order ), 'OA', index=True, readonly = False)
    oa_number = fields.Many2one('sale.order', 'OA', compute='_compute_oa_id_domain',index=True, readonly = False)

    #fields.Char('OA Number', readonly=False, default='') 
    iteam = fields.Char('Iteam', readonly=False)
    shade = fields.Char('Shade', readonly=False, default='')
    finish = fields.Char('Finish', readonly=False)

    #finish = o_data.finish #.replace('\n',' ')
    #finish = fields.Many2one('order.line.finish', "Finish",  required=True)
    #shade = o_data.shade
    
    #shade = fields.Many2one('sales.order.name.shade', "Shade",  required=True)
    #shade = fields.Selection([('bangladesh', 'Bangladesh'),('vietnam', 'Vietnam'),('pakistan', 'Pakistan')], string='Country', required=True, help='Country', default='bangladesh')
    #finish = fields.Char('Finish', readonly=False, default='')
    size = fields.Char('Size', readonly=False, default='')
    qty = fields.Char('Qty', readonly=False, default='')
    #qty = _compute_oa_id_domain.product_uom_qty
    #qty = sum(oa_number.mapped('sale_order_line.product_uom_qty'))

    batch_lot = fields.Char('Batch/Lot', readonly=False, default='')
    qc_person = fields.Many2one('hr.employee', "QC By",  required=True)
    # fil_qc_person = qc_person.filtered(lambda pr: pr.department_id == 'Quality Assurance')
    # emp_fil = self.qc_person.filtered(lambda x: x.department_id = 'Quality Assurance')
    
    pre_check_person = fields.Many2one('hr.employee', "Pre-Check By",  required=True) #all perosns form pre-check dept
   
    printing_person = fields.Many2one('hr.employee', "Print By",  required=True) #all perosns form packing dept
    

    date_to = fields.Date('Date to', readonly=False, default=lambda self: self._compute_to_date())
    file_data = fields.Binary(readonly=True, attachment=False)
    # oa_number = fields.Many2one('sale.order', 'OA', compute='_compute_oa_id_domain',index=True, readonly = False)

    @api.depends('oa_number')
    def _compute_oa_id_domain(self):
        raise UserError(('feefef'))
        oa_in_packing = self.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
        if oa_in_packing:
            domain = [('id', 'in', oa_in_packing.oa_id.ids),('company_id','=',self.env.company.id),('sales_type','=','oa')]
            self.oa_number = oa_in_packing.oa_id #[(6, 0, self.env['sale.order'].search(domain).ids)]
        else:
            self.oa_number = False


    
    # @api.depends('oa_number')
    # def _compute_oa_ids(self):
    #     oa_in_packing = self.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id)])
    #     oa_ids = oa_in_packing.oa_id.ids
    #     return oa_ids

    @api.depends('date_from')
    def _compute_from_date(self):
        dt_from = fields.datetime.now().replace(day = 1)
        return dt_from

    @api.depends('date_to')
    def _compute_to_date(self):
        # last_day_of_month = calendar.monthrange(fields.datetime.now().year, fields.datetime.now().month)[1]
        dt_to = fields.datetime.now()#.replace(day = last_day_of_month)
        return dt_to


    # @api.onchange('oa_number')
    # def _get_oa_wise_item(self):
    #     oa_in_packing = self.env['operation.details'].sudo().search([('next_operation','=','Packing Output'),('oa_id','!=',None),('state','not in',('closed','cancel')),('company_id','=',self.env.company.id),('oa_id.name', 'ilike', self.oa_number)])
    #     # oa_in_packing = oa_in_packing.filtered(lambda pr: self.oa_number in pr.oa_id)
    #     oa_ids = oa_in_packing.product_template_id.name
    #     return oa_ids

    

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
            if self.env.company.id == 1:
                return self.pi_xls_template(self, data=data)
            if self.env.company.id == 3:
                return self.pi_mt_xls_template(self, data=data)
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
        
        _row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        row_style = workbook.add_format({'bold': True, 'font_size': 12, 'font':'Arial', 'left': True, 'top': True, 'right': True, 'bottom': True})
        format_label_1 = workbook.add_format({'font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_2 = workbook.add_format({'font':'Calibri', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_3 = workbook.add_format({'font':'Calibri', 'font_size': 16, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True})
        
        format_label_4 = workbook.add_format({'font':'Arial', 'font_size': 12, 'valign': 'top', 'bold': True, 'left': True, 'top': True, 'right': True, 'bottom': True, 'text_wrap':True,})
        
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
            sheet.set_column(6, 6, 20)
            sheet.set_column(7, 7, 0)
            sheet.set_column(8, 8, 40)
            sheet.set_column(10, 10, 11)
            sheet.set_column(11, 11, 11)
            sheet.set_column(12, 12, 15)
            sheet.set_column(13, 13, 15)
            sheet.set_column(14, 14, 15)
            sheet.set_column(14, 20, 12)
            sheet.set_row(0, 30)

            
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
                        customer = "\n".join([orders.partner_id.name,"\n",payment_term])
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
        

