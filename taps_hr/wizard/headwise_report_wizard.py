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
_logger = logging.getLogger(__name__)

class HeadwisePDFReport(models.TransientModel):
    _name = 'salary.headwise.pdf.report'
    _description = 'Salary Headwise Report'    

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('BASIC',	'Basic'),
        ('HRA',	'HRA'),
        ('MEDICAL',	'Medical'),
        ('ARREAR',	'Arrear'),
        ('ATTBONUS',	'Attendance Bonus'),
        ('OT',	'Overtime'),
        ('CONVENCE',	'Convence'),
        ('FOOD',	'Food'),
        ('TIFFIN',	'Tiffin'),
        ('SNACKS',	'Strength Snacks'),
        ('CAR',	'Car'),
        ('OTHERS_ALW',	'Others Allowance'),
        ('INCENTIVE',	'Incentive'), 
        ('RPF',	'PF (Employer)'),
        ('PFR',	'PF (Employer)'),
        ('PFE',	'PF (Employee)'),
        ('AIT',	'TDS (AIT)'),
        ('BASIC_ABSENT',	'Basic Absent'),
        ('GROSS_ABSENT',	'Gross Absent'),
        ('LOAN',	'Loan'),
        ('ADV_SALARY',	'Advance Salary'),
        ('OTHERS_DED',	'Others Deduction'),
        ('NET',	'Net Payable'),],
        string='Report Type', required=False,
        help='By Salary Head Wise Report')
    
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
    
    employee_id = fields.Many2one(
        'hr.employee',  domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employee', index=True, readonly=False, ondelete="restrict")    
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)
    
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
                        'employee_type': False}

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
                        'employee_type': False}

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
                        'employee_type': False}

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
                        'employee_type': False}
                
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
                        'company_all': False}              
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
                        'company_all': self.company_all}
                
        return self.env.ref('taps_hr.action_salary_headwise_pdf_report').report_action(self, data=data)

    # Generate xlsx report
#     def action_generate_xlsx_report(self):
#         data = {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#         }
#         return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)

    
    def action_generate_xlsx_report(self):
        start_time = fields.datetime.now()
        if self.bank_id:
            if self.holiday_type == "employee":#employee  company department category
                #raise UserError(('sfefefegegegeeg'))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'company_all': False}

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'company_all': False}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'company_all': False}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'company_all': False}

            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'employee_type': self.employee_type,
                        'company_all': False}
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': self.bank_id.id,
                        'company_all': self.company_all}                
        
        domain = []
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('employee_id.category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('employee_id.category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('employee_id.category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('employee_id.category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('employee_id.category_ids.id', 'in',(25,42,43)))
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))                
        domain.append(('code', '=', 'NET'))
        
        #raise UserError((domain))
        docs = self.env['hr.payslip.line'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id))
        datefrom = data.get('date_from')
        dateto = data.get('date_to')
        bankname = self.bank_id.name
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
            
        
        #raise UserError((datefrom,dateto,bankname,categname))
        report_data = []
        emp_data = []
        slnumber=0
        for edata in docs:
            slnumber = slnumber+1
            emp_data = [
                slnumber,
                edata.employee_id.emp_id,
                edata.employee_id.name,
                format_date(self.env, edata.employee_id.joining_date),
                edata.employee_id.bank_account_id.acc_number,
                round(edata.total),
            ]
            report_data.append(emp_data)     
        
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#C8EAAB'})
        worksheet.merge_range('A1:F1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)

        report_small_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 14})
#         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        worksheet.merge_range('A2:F2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
        worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
#         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        
        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#EEED8A', 'font_size': 12})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})

        # set the width od the column
        
        worksheet.set_column(0, 5, 20)
        
        worksheet.write(4, 0, 'SL.', column_product_style)
        worksheet.write(4, 1, 'Emp ID', column_product_style)        
        worksheet.write(4, 2, 'Name', column_product_style)
        worksheet.write(4, 3, 'Joining Date', column_product_style)
        worksheet.write(4, 4, 'Account Number', column_product_style)
        worksheet.write(4, 5, 'Net Payable', column_product_style)
        col = 0
        row=5
        
        grandtotal = 0
        
        for line in report_data:
            col=0
            for l in line:
                if col>4:
                    grandtotal = grandtotal+l
                worksheet.write(row, col, l)
                col+=1
            row+=1
        
        #worksheet.write(4, 0, 'SL.', column_product_style)
        #raise UserError((row+1))
        worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        worksheet.write(row, 5, round(grandtotal), report_small_title_style)
        #raise UserError((datefrom,dateto,bankname,categname))
        workbook.close()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('%s-%s TRANSFER LIST' % (categname,bankname))),
            'target': 'self',
        }    

    
    
    

class HeadwiseReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.salary_headwise_pdf_template'
    _description = 'Salary Headwise Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
        if data.get('bank_id')==False:
            domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('employee_id.category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('employee_id.category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('employee_id.category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('employee_id.category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('employee_id.category_ids.id', 'in',(25,42,43)))
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))                
#         domain.append(('code', '=', 'NET'))        
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip.line'].search(domain).sorted(key = 'employee_id', reverse=False)
        
        otTotal = 0
        for de in docs:
            otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            round(otTotal),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip.line',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }
