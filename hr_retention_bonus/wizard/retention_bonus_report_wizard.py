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
_logger = logging.getLogger(__name__)

class RetentionPDFReport(models.TransientModel):
    _name = 'hr.retention.bonus.pdf.report'
    _description = 'Retention Bonus Scheme Report'    

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    report_type = fields.Selection([ 
        ('retentionbonus',	'Retention Bonus'),],
        string='Report Type', required=True,
        help='Report Type', default='retentionbonus')
    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(), required=True)   
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('companyall', 'By All Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
    # employee_id = fields.Many2one(
    #     'hr.employee',  domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employee', index=True, readonly=False, ondelete="restrict", default=lambda self: self.env.context.get('default_employee_id') or self.env.user.employee_id)
    employee_id = fields.Many2one(
        'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  domain="[('parent_id', '=', False)]", string='Department', readonly=False)
   
    employee_type = fields.Selection([
        ('staff', 'Staffs'),
        ('worker', 'Workers'),
        ('expatriate', 'Expatriates'),
        ('cstaff', 'C-Staffs'),
        ('cworker', 'C-Workers')],
        string='Employee Type', required=False)
    
    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED')],
        string='All Company', required=False)   
    
    file_data = fields.Binary(readonly=True, attachment=False) 

    
    # @staticmethod
    # def _get_year_list():
    #     current_year = datetime.today().year
    #     year_options = []
        
    #     for year in range(current_year - 1, current_year + 1):
    #         year_str = str(year+1)
    #         next_year = str(year+1)
    #         year_label = f'{year_str}'
    #         year_options.append((next_year, year_label))
    #     return year_options 
    
    @staticmethod
    def _get_year_list():
        current_year = datetime.today().year
        year_options = []
        
        for year in range(current_year - 3, current_year + 3):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((next_year, year_label))
        return year_options     


    @staticmethod
    def _get_default_year():
        current_year = datetime.today().year
        return str(current_year+1) 


    @api.depends('date_from')
    def _compute_from_date(self):
        if date.today().day>25:
            dt_from = fields.Date.today().strftime('%Y-%m-26')
        else:
            dt_from = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        return dt_from

    @api.depends('date_to')
    def _compute_to_date(self):
        if date.today().day>25:
            to_date = fields.Date.today() + relativedelta(months=1)
            dt_to = to_date.strftime('%Y-%m-25')
        else:
            dt_to = fields.Date.today().strftime('%Y-%m-25')
        return dt_to
    
    @api.depends('employee_id', 'holiday_type')
    def _compute_department_id(self):
        for holiday in self:
            if holiday.employee_id:
                holiday.department_id = holiday.employee_id.department_id
            elif holiday.holiday_type == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
            else:
                holiday.department_id = False
                
    #@api.depends('holiday_type')
    def _compute_from_holiday_type(self):
        for holiday in self:
            if holiday.holiday_type == 'employee':
                if not holiday.employee_id:
                    holiday.employee_id = self.env.user.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.department_id = False
            elif holiday.holiday_type == 'company':
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                holiday.category_id = False
                holiday.department_id = False
                holiday.employee_id = False
            elif holiday.holiday_type == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.holiday_type == 'category':
                if not holiday.category_id:
                    holiday.category_id = self.env.user.employee_id.category_ids
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.department_id = False
            #else:
            #    holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
    # generate PDF report
    def action_print_report(self):
        if self.report_type:
            if self.holiday_type == "employee":#employee  company department category
                #raise UserError((self.report_type))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id,
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}
                
            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': self.employee_type,
                        'company_all': False,
                        'year': self.year}              
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'year': self.year}
                
#         return self.env.ref('taps_hr.action_kpi_objective_pdf_report').report_action(self, data=data)
        # if self.report_type == 'kpi':
        #     return self.env.ref('taps_hr.action_kpi_objective_pdf_report').report_action(self, data=data)
        # else:
        #     raise UserError(('This Report are not PDF Format'))

    
    
    def action_generate_xlsx_report(self):
        if self.report_type:
        # if self.report_type == 'plan':
        #     start_time = fields.datetime.now()
            if self.holiday_type == "employee":#employee  company department category
                #raise UserError(('sfefefegegegeeg'))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'employee_type': self.employee_type,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': self.company_all,
                        'year': self.year}
        if self.report_type == 'retentionbonus':
            return self.retention_bonus_xls_template(self, data=data)

    def retention_bonus_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
        # if data.get('date_from'):
        #     domain.append(('date', '>=', data.get('date_from')))
        # if data.get('date_to'):
        #     domain.append(('date_to', '<=', data.get('date_to')))
        # if data.get('year'):
        #     # raise UserError((data.get('year')))
        #     deadlines = str(data.get('year') + '-03-31')
        #     domain.append(('date', '=', deadlines)) 
        if data.get('mode_company_id'):
            domain.append(('bonus_id.employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('bonus_id.department_id.parent_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('bonus_id.employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('bonus_id.employee_id.id', '=', data.get('employee_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('bonus_id.employee_id.category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('bonus_id.employee_id.category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('employee_id.category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('bonus_id.employee_id.category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('bonus_id.employee_id.category_ids.id', 'in',(25,42,43)))
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('bonus_id.employee_id.company_id.id', 'in',(1,2,3,4)))                
        
        # docs = self.env['hr.retention.bonus'].search(domain).sorted(key = 'employee_id', reverse=False)

        
        datefrom = data.get('date_from')

        # raise UserError((data.get('year')))
        year_from = int(data.get('year'))-1
        year_to = int(data.get('year'))
        datefrom = date.today().replace(day=1).replace(month=4).replace(year=year_from)
        dateto = date.today().replace(month=3).replace(day=31).replace(year=year_to)
        #(date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        # year_ = int(datefrom.strftime('%Y'))
        
        # raise UserError((datefrom,dateto))
        docs = self.env['hr.retention.bonus.line'].search(domain)#.sorted(key = 'employee_id', reverse=False)
        docs = docs.filtered(lambda x: x.date >= datefrom and x.date <= dateto)

        
        # raise UserError((docs[0].date.year))
        

        dateto = data.get('date_to')
        
        categname=[]
        if self.employee_type =='staff':
            categname='Staffs'
        if self.employee_type =='expatriate':
            categname='Expatriates'
        if self.employee_type =='worker':
            categname='Workers'
        if self.employee_type =='cstaff':
            categname='C-Staffs'
        if self.employee_type =='cworker':
            categname='C-Workers'
            
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        report_title_style = workbook.add_format({'bold': True, 'font_size': 11})
        report_title_style2 = workbook.add_format({'font_size': 11, 'num_format': 'mmm-yy'})
        report_title_style3 = workbook.add_format({'font_size': 11, 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        # worksheet.merge_range('A1:F1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
        worksheet.merge_range('B2:C2', ('April to Mar (%s - %s)' % (str(year_from),str(year_to))), report_title_style)
        
        report_small_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 14})
        # worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('D2:E2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_title_style)
        # worksheet.merge_range('D2:E2', (str(year_to), '%Y-%m-%d').strftime('%B  %Y')), report_title_style)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_title_style)
        
        column_product_style = workbook.add_format({'bold': True, 'font_size': 11})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'font_size': 11, 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})

        # set the width od the column
        
        worksheet.set_column(1, 1, 25)
        worksheet.set_column(2, 2, 20)
        worksheet.set_column(3, 3, 14)
        
        # worksheet.write(4, 0, 'SL.', column_product_style)
        worksheet.write(4, 1, 'Employee Name', column_product_style)        
        worksheet.write(4, 2, 'Payment Start DT', column_product_style)
        worksheet.write(4, 3, 'Amount', column_product_style)
        worksheet.write(4, 4, 'Apr', column_product_style)
        worksheet.write(4, 5, 'May', column_product_style)
        worksheet.write(4, 6, 'Jun', column_product_style)
        worksheet.write(4, 7, 'Jul', column_product_style)
        worksheet.write(4, 8, 'Aug', column_product_style)
        worksheet.write(4, 9, 'Sep', column_product_style)
        worksheet.write(4, 10, 'Oct', column_product_style)
        worksheet.write(4, 11, 'Nov', column_product_style)
        worksheet.write(4, 12, 'Dec', column_product_style)
        worksheet.write(4, 13, 'Jan', column_product_style)
        worksheet.write(4, 14, 'Feb', column_product_style)
        worksheet.write(4, 15, 'Mar', column_product_style)
        col = 1
        row=5

        employees = docs.mapped('employee_id')
        for emp in employees:
            emp_docs = docs.filtered(lambda x: x.employee_id.id == emp.id)
            # raise UserError((emp_docs[0].employee_id.id))
            for l in emp_docs:
                # raise UserError((l.date.month))
                # for l in lines:
                if col == 1: 
                    worksheet.write(row, col, l.employee_id.display_name,)
                    col += 1
                if col == 2: 
                    worksheet.write(row, col, l.payment_date, report_title_style2)
                    col += 1
                if col == 3: 
                    worksheet.write(row, col, l.bonus_amount,report_title_style3)
                    col += 1
                    #in (4,5,6,7,8,9,10,11,12,13,14,15)
                if col == 4 and  l.date.month == 4:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 5 and  l.date.month == 5:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 6 and  l.date.month == 6:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 7 and  l.date.month == 7:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 8 and  l.date.month == 8:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 9 and  l.date.month == 9:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 10 and  l.date.month == 10:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 11 and  l.date.month == 11:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 12 and  l.date.month == 12:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 13 and  l.date.month == 1:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 14 and  l.date.month == 2:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                else:
                    col += 1
                if col == 15 and  l.date.month == 3:
                    worksheet.write(row, col, l.amount, report_title_style3)
                    col += 1
                
                col = 1
            
            row +=1

        worksheet.write(row, 3, '=SUM(D{0}:D{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 4, '=SUM(E{0}:E{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 5, '=SUM(F{0}:F{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 6, '=SUM(G{0}:G{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 7, '=SUM(H{0}:H{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 8, '=SUM(I{0}:I{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 9, '=SUM(J{0}:J{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 10, '=SUM(K{0}:K{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 11, '=SUM(L{0}:L{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 12, '=SUM(M{0}:M{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 13, '=SUM(N{0}:N{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 14, '=SUM(O{0}:O{1})'.format(5, row), column_issued_style)
        worksheet.write(row, 15, '=SUM(P{0}:P{1})'.format(5, row), column_issued_style)
        

        
        #raise UserError((datefrom,dateto,bankname,categname))
        workbook.close()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Retention Bonus')),
            'target': 'self',
        }

