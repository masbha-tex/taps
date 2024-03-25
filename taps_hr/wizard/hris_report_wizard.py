import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date, format_datetime
from dateutil.relativedelta import relativedelta
import re
import math

_logger = logging.getLogger(__name__)

class HRISPDFReport(models.TransientModel):
    _name = 'hris.pdf.report'
    _description = 'HRIS Report'    

    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    report_type = fields.Selection([
        ('employee_profile',	'Employee Profile'),
        ('joining',	'Joining Letter'),        
        ('appointment',	'Appointment Letter'),
        ('confirmation',	'Confirmation Letter'),
        ('trail_extension',	'Extension of Probation Period'),
        ('no_dues',	'No Dues Certificate'),
        ('pf',	'Monthly PF Statement'),
        ('loan',	'Loan Application'),
        ('pf_loan',	'PF Loan Application'),
        ('marriage',	'Marriage Certificate'),
        ('ac_opening',	'Account Opening Letter'),
        ('shift',	'Weekly Shift Schedule'),
        ('attcalendar',	'Attendance Calendar'),
        ('training',	'Worker Training Program'), 
        ('birthcalendar',	'Birthday Calendar'),
        ('anniversarycalendar', 'Anniversary Calendar'),
        ('retentionmatrix', 'Retention Risk Matrix'),
#         ('leave',	'Leave Form'),
        ('retentionincentive',	'Retention Incentive'),
        ('employeerelation', 'Employee Relationship'),
        ('employeeresign', 'Employee Resign Data'),
        ('employeejoining', 'Employee Joining Data'),],
        string='Report Type', required=True, default='employee_profile',
        help='By HRIS Report')
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('companyall', 'By All Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Mode Type', required=True, default='employee',
        help='By Employee: Report for individual Employee, By Employee Tag: Report for group of employees in category')
    
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
    employee_id = fields.Many2one(
        'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
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
        ('cworker', 'C-workers')],
        string='Employee Type', required=False)
    
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)     
    
    file_data = fields.Binary(readonly=True, attachment=False)

    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED')],
        string='All Company', required=False) 

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
    
    @api.depends('employee_id', 'mode_type')
    def _compute_department_id(self):
        for hris in self:
            if hris.employee_id:
                hris.department_id = hris.employee_id.department_id
            elif hris.mode_type == 'department':
                if not hris.department_id:
                    hris.department_id = self.env.user.employee_id.department_id
            else:
                hris.department_id = False
                
    #@api.depends('mode_type')
    def _compute_from_mode_type(self):
        for hris in self:
            if hris.mode_type == 'employee':
                if not hris.employee_id:
                    hris.employee_id = self.env.user.employee_id
                hris.mode_company_id = False
                hris.category_id = False
                hris.department_id = False
            elif hris.mode_type == 'company':
                if not hris.mode_company_id:
                    hris.mode_company_id = self.env.company.id
                hris.category_id = False
                hris.department_id = False
                hris.employee_id = False
            elif hris.mode_type == 'department':
                if not hris.department_id:
                    hris.department_id = self.env.user.employee_id.department_id
                hris.employee_id = False
                hris.mode_company_id = False
                hris.category_id = False
            elif hris.mode_type == 'category':
                if not hris.category_id:
                    hris.category_id = self.env.user.employee_id.category_ids
                hris.employee_id = False
                hris.mode_company_id = False
                hris.department_id = False
            #else:
            #    hris.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
    # generate PDF report
    def action_print_report(self):
        if self.report_type:
            if self.mode_type == "employee":#employee  company department category
                #raise UserError((self.report_type))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id,
                        'report_type': self.report_type,
                        'bank_id': self.bank_id.id,
                        'types': self.types,
                        'employee_type': self.employee_type}

            if self.mode_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': self.bank_id.id,
                        'types': self.types,
                        'employee_type': self.employee_type}

            if self.mode_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': self.bank_id.id,
                        'types': self.types,
                        'employee_type': self.employee_type}

            if self.mode_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': self.bank_id.id,
                        'types': self.types,
                        'employee_type': self.employee_type}
            if self.mode_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': self.bank_id.id,
                        'types': self.types,
                        'employee_type': self.employee_type}                
        if self.report_type == 'employee_profile':
            return self.env.ref('taps_hr.action_hris_employee_card_pdf_report').report_action(self, data=data)
        if self.report_type == 'joining':
            return self.env.ref('taps_hr.action_hris_joining_pdf_report').report_action(self, data=data)
        if self.report_type == 'appointment':
            return self.env.ref('taps_hr.action_hris_appointment_pdf_report').report_action(self, data=data)
        if self.report_type == 'confirmation':
            return self.env.ref('taps_hr.action_hris_confirmation_pdf_report').report_action(self, data=data)
        if self.report_type == 'trail_extension':
            return self.env.ref('taps_hr.action_hris_trail_extension_pdf_report').report_action(self, data=data)
        if self.report_type == 'no_dues':
            return self.env.ref('taps_hr.action_hris_no_dues_pdf_report').report_action(self, data=data)
        if self.report_type == 'pf':
            return self.env.ref('taps_hr.action_hris_pf_pdf_report').report_action(self, data=data)
        if self.report_type == 'loan':
            return self.env.ref('taps_hr.action_hris_loan_pdf_report').report_action(self, data=data)
        if self.report_type == 'pf_loan':
            return self.env.ref('taps_hr.action_hris_pf_loan_pdf_report').report_action(self, data=data)
        if self.report_type == 'marriage':
            return self.env.ref('taps_hr.action_hris_marriage_pdf_report').report_action(self, data=data)
        if self.report_type == 'ac_opening':
            return self.env.ref('taps_hr.action_ac_opening_pdf_report').report_action(self, data=data)
        if self.report_type == 'shift':
            return self.env.ref('taps_hr.action_hris_shift_pdf_report').report_action(self, data=data)
        if self.report_type == 'attcalendar':
            return self.env.ref('taps_hr.action_hris_attcalendar_pdf_report').report_action(self, data=data)
        if self.report_type == 'training':
            return self.env.ref('taps_hr.action_hris_training_pdf_report').report_action(self, data=data)
        if self.report_type == 'birthcalendar':
            return self.env.ref('taps_hr.action_hris_birth_calendar_pdf_report').report_action(self, data=data)
        if self.report_type == 'retentionincentive':
            return self.env.ref('taps_hr.action_hris_retentionincentive_pdf_report').report_action(self, data=data)
        if self.report_type == 'anniversarycalendar':
            return self.env.ref('taps_hr.action_hris_anniversary_calendar_pdf_report').report_action(self, data=data)
        if self.report_type == 'retentionmatrix':
            return self.env.ref('taps_hr.action_hris_retention_risk_matrix_pdf_report').report_action(self, data=data)
        else:
            raise UserError(('This Report are not PDF Format'))
            

    def action_generate_xlsx_report(self):
        
        
        if self.mode_type == "employee":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': self.employee_id.id,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}

        if self.mode_type == "company":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': self.mode_company_id.id, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': False, 
                    'company_all': False,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}

        if self.mode_type == "department":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': self.department_id.id, 
                    'category_id': False, 
                    'employee_id': False,
                    'company_all': False,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}

        if self.mode_type == "category":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': self.category_id.id, 
                    'employee_id': False,
                    'company_all': False,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}
        if self.mode_type == "emptype":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': False, 
                    'company_all': False,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}
        if self.mode_type == "companyall":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': False, 
                    'company_all': self.company_all,
                    'report_type': self.report_type,
                    'bank_id': self.bank_id.id,
                    'types': self.types,
                    'employee_type': self.employee_type}
        if self.report_type == 'employeerelation':
            return self.relationship_xls_template(self, data=data)
        if self.report_type == 'employeeresign':
            return self.resign_xls_template(self, data=data)
        if self.report_type == 'employeejoining':
            return self.joining_xls_template(self, data=data)
        # if self.report_type == 'employeerelationmatrix':
        #     return self.relationship_matrix_xls_template(self, data=data)
        else:
            raise UserError(('This Report are not XLSX Format')) 



    def relationship_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
        # if data.get('date_from'):
        #     domain.append(('date_from', '>=', data.get('date_from')))
        # if data.get('date_to'):
        #     domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('company_id.id', 'in',(1,2,3,4))) 
            
        
        domain.append(('active', 'in',(True)))
        # datefrom = data.get('date_from')
        # dateto = data.get('date_to')
        #raise UserError((domain))
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        # docs1 = self.env['hr.employee.relation'].search(domain)
        #raise UserError((docs.id))
        # datefrom = data.get('date_from')
        # dateto = data.get('date_to')
        # bankname = self.bank_id.name
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
            if edata.employee_relation:
                slnumber = slnumber+1
                emp_data = [
                    slnumber,
                    edata.emp_id,
                    edata.name,
                    edata.company_id.name,
                    edata.department_id.name,
                    edata.employee_relation.name,
                    edata.relationship_id.emp_id,
                    edata.relationship_id.name,
                    edata.relationship_id.company_id.name,
                    edata.relationship_id.department_id.name,
                    
                ]
                report_data.append(emp_data)     
        
#Retationship
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(('Employee Relationship'))
        worksheet.hide_gridlines(2)
        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#714B62', 'font_color':'#FFFFFF'})
        report_title_style2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14, 'bg_color': '#343A40', 'font_color':'#FFFFFF'})
        worksheet.merge_range('A1:J1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
        worksheet.merge_range('A2:J2', 'Employee Relationship Status', report_title_style2)

        report_small_title_style = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True})
        report_small_title_style2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'bg_color': '#714B62', 'font_color':'#FFFFFF','left': True,'bold': True, 'top': True, 'right': True, 'bottom': True})
#         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('A2:F2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
#         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        
        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF'})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})

        worksheet.freeze_panes(3, 0)

        # set the width od the column
        
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 7)
        worksheet.set_column(2, 2, 23)
        worksheet.set_column(3, 3, 10)
        worksheet.set_column(4, 5, 26)
        worksheet.set_column(6, 6, 7)
        worksheet.set_column(7, 7, 23)
        worksheet.set_column(8, 8, 10)
        worksheet.set_column(9, 9, 26)
        
        # worksheet.set_row(2, 20)
        
        
        worksheet.write(2, 0, 'SL.', column_product_style)
        worksheet.write(2, 1, 'ID', column_product_style)        
        worksheet.write(2, 2, 'Name', column_product_style)
        worksheet.write(2, 3, 'Unit', column_product_style)
        worksheet.write(2, 4, 'Section', column_product_style)
        worksheet.write(2, 5, 'Relation', column_product_style)
        worksheet.write(2, 6, 'ID', column_product_style)
        worksheet.write(2, 7, 'Name', column_product_style)
        worksheet.write(2, 8, 'Unit', column_product_style)
        worksheet.write(2, 9, 'Section', column_product_style)
        col = 0
        row=3
        
        # grandtotal = 0
        for line in report_data:
            col = 0
            for l in line:
                if col == 5:
                    worksheet.write(row, col, l, report_small_title_style2)
                    col+=1
                elif (col in (0,1,2,3,4,6,7,8,9)):
                    worksheet.write(row, col, l, report_small_title_style)
                    col+=1
            row+=1


        
        # for line in report_data:
        #     col=0
        #     for l in line:
        #         if col>4:
        #             grandtotal = grandtotal+l
        #         worksheet.write(row, col, l)
        #         col+=1
        #     row+=1
        
        # worksheet.write(4, 0, 'SL.', column_product_style)
        # raise UserError((row+1))
        # worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        # worksheet.write(row, 5, round(grandtotal), report_small_title_style)
        # raise UserError((datefrom,dateto,bankname,categname))

        
        worksheet1 = workbook.add_worksheet(('Relationship Matrix'))
        worksheet1.hide_gridlines(2)
        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#714B62', 'font_color':'#FFFFFF'})
        report_title_style2 = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 14, 'bg_color': '#343A40', 'font_color':'#FFFFFF'})
        worksheet1.merge_range('A1:I1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
        worksheet1.merge_range('A2:I2', 'Employee Relationship Martix', report_title_style2)
        

        report_small_title_style = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True})
        report_small_title_style2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'bg_color': '#714B62', 'font_color':'#FFFFFF','left': True,'bold': True, 'top': True, 'right': True, 'bottom': True})

        
        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF'})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'text_wrap':True,'align': 'center', 'bold': True, 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter', 'bg_color': '#EDEDED', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        column_issued_style1 = workbook.add_format({'text_wrap':True,'align': 'center', 'bold': True, 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter', 'bg_color': '#714B62', 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        column_issued_style2 = workbook.add_format({'text_wrap':True,'align': 'center', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True,'valign': 'vcenter', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})


        # set the width od the column
        
        worksheet1.set_column(0, 0, 12)
        worksheet1.set_column(1, 1, 7)
        worksheet1.set_column(2, 2, 30)
        worksheet1.set_column(3, 3, 7)
        worksheet1.set_column(4, 9, 15)
        
        # worksheet.set_row(2, 20)

        # set the width od the merge_range (row_num, col_num, row_num, col_num, '', column_style)

        # worksheet1.merge_range(2, 0, 3, 0, 'ALL',column_issued_style1)
        # worksheet1.merge_range(2, 1, 3, 2, 'Relation Defined',column_issued_style)
        # worksheet1.merge_range(2, 3, 3, 3, 'No',column_issued_style)
        # worksheet1.merge_range(2, 9, 3, 9, 'Remarks',column_issued_style)

        # worksheet1.merge_range('E13:G13', 'Employees are in Same Unit', column_issued_style)
        # worksheet1.merge_range('H13:I13', 'Employees are in Other Unit', column_issued_style)

        # worksheet1.merge_range(12, 0, 13, 0, 'BUTTON - WORKER',column_issued_style1)
        # worksheet1.merge_range(12, 1, 13, 2, 'Relation Defined',column_issued_style)
        # worksheet1.merge_range(12, 3, 13, 3, 'No',column_issued_style)
        # worksheet1.merge_range(12, 9, 13, 9, 'Remarks',column_issued_style)
        #title
        # no = 1
        # docs

        report_data = []
        emp_data = []
        slnumber=0
        company = None
        row_ = 3
        # company_ids = docs.mapped('company_id')
        head_row = 3
        for a in (1,2,3,4):
            report_data = []
            company_id = None
            head_company = None
            if a == 1:
                company_ids = docs.mapped('company_id')
                if len(company_ids) > 1:
                    rel_data = docs.filtered(lambda x: x.company_id.id in (1,2,3))
                    head_company = 'ALL'
            if a == 2:
                rel_data = docs.filtered(lambda x: x.company_id.id == 1)
                head_company = 'ZIPPER'
            if a == 3:
                rel_data = docs.filtered(lambda x: x.company_id.id == 3)
                head_company = 'METAL TRIMS'
            if a == 4:
                rel_data = docs.filtered(lambda x: x.company_id.id == 2)
                head_company = 'COMMON OFFICE'
            
            if rel_data:
                relation = None
                no_count = same_section = other_section = direct_reporting = other_unit = 1
                
                for i in range(7):
                    if i == 0:
                        relation = 'Spouse'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        # raise UserError((get_relation))
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                               
                    if i == 1:
                        relation = 'Brother to Brother/Sister'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                    if i == 2:
                        relation = 'Parents/In law to Son/Daughter'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        # raise UserError((get_relation))
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                       
                    if i == 3:
                        relation = 'Uncle to Nephew/Niece'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                    if i == 4:
                        relation = 'Cousin Brother/Sister'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                        
                    if i == 5:
                        relation = 'Brother In-Law/Sister In-Law'
                        no_count = same_section = other_section = direct_reporting = other_unit = 0

                        get_relation = rel_data.filtered(lambda x: x.employee_relation.name == relation)
                        for rel in get_relation:
                            if (rel.company_id.id == rel.relationship_id.company_id.id):
                                if (rel.department_id.id == rel.relationship_id.department_id.id):
                                    same_section += 1
                                else:
                                    other_section += 1
                                if (rel.id == rel.relationship_id.parent_id.id):
                                    direct_reporting += 1
                            else:
                                other_unit += 1
                        no_count = same_section + other_section + other_unit
                        # no_count = same_section + other_section + direct_reporting + other_unit
                        
                    # if i == 6:
                    #     relation = ''
                    
                    emp_data = [
                            relation,
                            no_count,
                            same_section,
                            other_section,
                            direct_reporting,
                            other_unit,
                            '',
                        ]
                    report_data.append(emp_data)
                
                worksheet1.merge_range(head_row-1, 4, head_row-1, 6, 'Employees are in Same Unit', column_issued_style1)

                worksheet1.merge_range(head_row-1, 0, head_row, 0, head_company, column_issued_style1)

                # worksheet1.write(head_row, 0, head_company, column_issued_style1)
                worksheet1.merge_range(head_row-1, 1, head_row, 1, 'SL', column_issued_style1)        
                worksheet1.merge_range(head_row-1, 2, head_row, 2, 'Relation Defined', column_issued_style1)
                worksheet1.merge_range(head_row-1, 3, head_row, 3, 'No', column_issued_style1)
                worksheet1.write(head_row, 4, 'Same Section', column_issued_style1)
                worksheet1.write(head_row, 5, 'Other Section', column_issued_style1)
                worksheet1.write(head_row, 6, 'Direct reporting', column_issued_style1)
                worksheet1.merge_range(head_row-1, 7, head_row, 7, 'Employees are in Others Unit', column_issued_style1)
                worksheet1.merge_range(head_row-1, 8, head_row, 8, 'Remarks', column_issued_style1)
    
                rec_n = 1
                row_ = head_row + 1
                head_row += 9
                start_row = row_
                for rec in report_data:
                    if rec_n == 7:
                        worksheet1.write(row_, 1, '')
                        worksheet1.write(row_, 3, '=SUM(D{0}:D{1})'.format(start_row, row_), column_issued_style)
                        worksheet1.write(row_, 4, '=SUM(E{0}:E{1})'.format(start_row, row_), column_issued_style)
                        worksheet1.write(row_, 5, '=SUM(F{0}:F{1})'.format(start_row, row_), column_issued_style)
                        worksheet1.write(row_, 6, '=SUM(G{0}:G{1})'.format(start_row, row_), column_issued_style)
                        worksheet1.write(row_, 7, '=SUM(H{0}:H{1})'.format(start_row, row_), column_issued_style)
                    
                    else:
                        worksheet1.write(row_, 1, rec_n, column_issued_style)
                        worksheet1.write(row_, 2, rec[0], column_issued_style)
                        worksheet1.write(row_, 3, rec[1], column_issued_style)
                        worksheet1.write(row_, 4, rec[2], column_issued_style)
                        worksheet1.write(row_, 5, rec[3], column_issued_style)
                        worksheet1.write(row_, 6, rec[4], column_issued_style)
                        worksheet1.write(row_, 7, rec[5], column_issued_style)
                        worksheet1.write(row_, 8, rec[6], column_issued_style)
                    row_ += 1
                    rec_n += 1
                    
                row_ += 9
        
        col = 0
        row=3
        
        workbook.close()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Employee Relationship')),
            'target': 'self',
        }    

  


    def resign_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
                 
        if data.get('date_from'):
            domain.append(('resign_date', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('resign_date', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))

        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('company_id.id', 'in',(1,2,3)))
            
        
        domain.append(('active', '=', False))
        # datefrom = data.get('date_from')
        # dateto = data.get('date_to')
        #raise UserError((domain))
        # docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)

        docs = self.env['hr.employee'].search(domain).sorted(key=lambda r: r.resign_date or '', reverse=False)
        
        # docs = docs.sorted(key = 'date_to', reverse=False)
        # docs1 = self.env['hr.contract'].search(domain).sorted(key = 'id', reverse=False)
        # docs1 = self.env['hr.employee.relation'].search(domain)
        #raise UserError((docs.id))
        datefrom = data.get('date_from')
        dateto = data.get('date_to')
        # bankname = self.bank_id.name
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

        
        report_data = []
        emp_data = []
        slnumber=0
        for edata in docs:
            status = ''
            if edata.resign_date > edata.probation_date:
                status = 'CONFIRMED'
            else:
                status = 'NOT CONFIRMED'

            if edata.performance_rated:
                performance = edata.performance_rated
            else:
                performance = ''

            if edata.departure_reason:
                reason = edata.departure_reason
            else:
                reason = ''
          
            slnumber = slnumber+1
            emp_data = [
                slnumber,
                edata.emp_id,
                edata.name,
                edata.company_id.name,
                edata.category_ids.name,
                edata.department_id.parent_id.name,
                edata.department_id.name,
                edata.job_id.name,
                edata.grade,
                edata.joining_date,
                edata.resign_date,
                edata.service_length,
                edata.gender,
                edata.contract_id.wage,
                performance,
                reason,
                status,
            ]
            report_data.append(emp_data)     
    
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(('Resign Employee'))

        report_title_style = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#714B62', 'font_color':'#FFFFFF'})
        report_title_style2 = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#343A40', 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        worksheet.merge_range('A1:Q1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
        # sum_formula_wage = '=SUM(P{0}:P{1})'.format(4,report_data + 3)
        # worksheet.merge_range('A1:H1', 'TEX ZIPPERS (BD) LIMITED - Total Wage: {}'.format(sum_formula_wage), report_title_style)

        worksheet.merge_range('A2:Q2', 'Employee Resign Data - Total Employees: {}'.format(slnumber), report_title_style2)
        # worksheet.merge_range('A3:Q3', '', report_title_style2)
        worksheet.merge_range('A3:Q3', 'From: {} To: {}'.format(datefrom, dateto), report_title_style2)

        report_small_title_style = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        report_small_title_style2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': 'd-mmm-yy'})
#         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('I2:J2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style2)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
#         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        
        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})
        merge_format_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 12, 'font_color':'#FFFFFF'})
        merge_format_.set_text_wrap()

        worksheet.freeze_panes(4, 5)

        # set the width od the column
        
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 7)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 4, 18)
        worksheet.set_column(5, 7, 26)
        worksheet.set_column(8, 8, 8)
        worksheet.set_column(9, 10, 12)
        worksheet.set_column(11, 11, 23)
        worksheet.set_column(12, 12, 8)
        worksheet.set_column(13, 16, 20)
        
        # worksheet.set_row(2, 20)
        
        
        worksheet.write(3, 0, 'SL.', column_product_style)
        worksheet.write(3, 1, 'ID', column_product_style)        
        worksheet.write(3, 2, 'Name', column_product_style)
        worksheet.write(3, 3, 'Unit', column_product_style)
        worksheet.write(3, 4, 'Category', column_product_style)
        worksheet.write(3, 5, 'Department', column_product_style)
        worksheet.write(3, 6, 'Section', column_product_style)
        worksheet.write(3, 7, 'Designation', column_product_style)
        worksheet.write(3, 8, 'Grade', column_product_style)
        worksheet.write(3, 9, 'Joining Date', column_product_style)
        worksheet.write(3, 10, 'Resign Date', column_product_style)
        worksheet.write(3, 11, 'Service Length', column_product_style)
        worksheet.write(3, 12, 'Gender', column_product_style)
        worksheet.write(3, 13, 'Last Draw Salary', column_product_style)
        worksheet.write(3, 14, 'Performance Rated', column_product_style)
        worksheet.write(3, 15, 'Reason For Leave', column_product_style)
        worksheet.write(3, 16, 'Confirmation Status', column_product_style)
        
        col = 0
        row=4
        
        # grandtotal = 0
        for line in report_data:
            col = 0
            # wei = None
            for l in line:
                if col == 9:
                    worksheet.write(row, col, l, report_small_title_style2)
                    col+=1
                elif col == 10:
                    worksheet.write(row, col, l, report_small_title_style2)
                    col+=1
                # elif col == 15 and (l == False):
                #     worksheet.write(row, col, '', report_small_title_style)
                #     col+=1
                # elif col == 15 and (l != ''):
                #     worksheet.write(row, col, l, report_small_title_style)
                #     col+=1
                elif (col in (0,1,2,3,4,5,6,7,8,11,12,13,14,15,16)):
                    worksheet.write(row, col, l, report_small_title_style)
                    col+=1
            row+=1
          
        worksheet.write(row, 1, row-4, column_issued_style)
        worksheet.write(row, 13, '=SUM(N{0}:N{1})'.format(5, row), column_issued_style)
        row+=2

        #allcompany == 
        if data.get('company_all'):

            all_workers = docs.filtered(lambda x: x.category_ids.name in ('Worker', 'Z-Worker', 'B-Worker', 'C-Zipper Worker', 'C-Button Worker', 'C-Worker'))
            all_staffs = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'B-Staff', 'Z-Staff', 'Z-Expatriate', 'Expatriate', 'B-Expatriate', 'C-Button Staff', 'C-Zipper Staff', 'C-Staff'))
            workercount = len(all_workers)
            staffcount = len(all_staffs)
            
            workerwage = sum(all_workers.mapped('contract_id.wage'))
            staffwage = sum(all_staffs.mapped('contract_id.wage'))
            #worker
            worksheet.write(row, 1, workercount, column_product_style)
            worksheet.write(row, 2, 'WORKERS SUMMARY', merge_format_)
            worksheet.write(row, 3, workerwage, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount, column_product_style)
            worksheet.write(row, 6, 'STAFF SUMMARY', merge_format_)
            worksheet.write(row, 7, staffwage, column_product_style)
            row+=1
    
     #Zipper      
            
            all_workers_z = docs.filtered(lambda x: x.category_ids.name in ('Z-Worker'))
            all_staffs_z = docs.filtered(lambda x: x.category_ids.name in ('Z-Staff', 'Z-Expatriate'))
            workercount_z = len(all_workers_z)
            staffcount_z = len(all_staffs_z)
              
    
            c_male_workers_z = all_workers_z.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_workers_z = all_workers_z.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_workers_z = all_workers_z.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_workers_z = all_workers_z.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_workers_cost_z = sum(c_male_workers_z.mapped('contract_id.wage'))
            c_female_workers_cost_z = sum(c_female_workers_z.mapped('contract_id.wage'))
            nc_male_workers_cost_z = sum(nc_male_workers_z.mapped('contract_id.wage'))
            nc_female_workers_cost_z = sum(nc_female_workers_z.mapped('contract_id.wage'))
    
            c_male_staff_cost_z = sum(c_male_staff_z.mapped('contract_id.wage'))
            c_female_staff_cost_z = sum(c_female_staff_z.mapped('contract_id.wage'))
            nc_male_staff_cost_z = sum(nc_male_staff_z.mapped('contract_id.wage'))
            nc_female_staff_cost_z = sum(nc_female_staff_z.mapped('contract_id.wage'))
            #worker
            w_wages_sum_z = sum([*c_male_workers_z.mapped('contract_id.wage'),*c_female_workers_z.mapped('contract_id.wage'),*nc_male_workers_z.mapped('contract_id.wage'),*nc_female_workers_z.mapped('contract_id.wage')])
            #staff
            s_wages_sum_z = sum([c_male_staff_cost_z,c_female_staff_cost_z,nc_male_staff_cost_z,nc_female_staff_cost_z])
            #all
            
            # wages_sum = sum([c_male_staff_cost,c_female_staff_cost,nc_male_staff_cost,nc_female_staff_cost,c_male_workers_cost,c_female_workers_cost,nc_male_workers_cost,nc_female_workers_cost])
            # wages_sum = sum([all_emp])
            # worksheet.write('N2', wages_sum, report_title_style2)
    
            
            #worker
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_z, column_product_style)
            worksheet.write(row, 2, 'Zipper SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_z, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_z, column_product_style)
            worksheet.write(row, 6, 'Zipper SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_z, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_z, report_small_title_style)
            row+=1
    
    #Metal_Trims
    
            all_workers_m = docs.filtered(lambda x: x.category_ids.name in ('B-Worker'))
            all_staffs_m = docs.filtered(lambda x: x.category_ids.name in ('B-Staff', 'B-Expatriate'))
            workercount_m = len(all_workers_m)
            staffcount_m = len(all_staffs_m)
              
    
            c_male_workers_m = all_workers_m.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_workers_m = all_workers_m.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_workers_m = all_workers_m.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_workers_m = all_workers_m.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_workers_cost_m = sum(c_male_workers_m.mapped('contract_id.wage'))
            c_female_workers_cost_m = sum(c_female_workers_m.mapped('contract_id.wage'))
            nc_male_workers_cost_m = sum(nc_male_workers_m.mapped('contract_id.wage'))
            nc_female_workers_cost_m = sum(nc_female_workers_m.mapped('contract_id.wage'))
    
            c_male_staff_cost_m = sum(c_male_staff_m.mapped('contract_id.wage'))
            c_female_staff_cost_m = sum(c_female_staff_m.mapped('contract_id.wage'))
            nc_male_staff_cost_m = sum(nc_male_staff_m.mapped('contract_id.wage'))
            nc_female_staff_cost_m = sum(nc_female_staff_m.mapped('contract_id.wage'))
            #worker
            w_wages_sum_m = sum([*c_male_workers_m.mapped('contract_id.wage'),*c_female_workers_m.mapped('contract_id.wage'),*nc_male_workers_m.mapped('contract_id.wage'),*nc_female_workers_m.mapped('contract_id.wage')])
            
            #staff
            s_wages_sum_m = sum([c_male_staff_cost_m,c_female_staff_cost_m,nc_male_staff_cost_m,nc_female_staff_cost_m])
    
            
    
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_m, column_product_style)
            worksheet.write(row, 2, 'Metal Trim SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_m, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_m, column_product_style)
            worksheet.write(row, 6, 'Metal Trim SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_m, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_m, report_small_title_style)
            row+=1
    
    #Head Office
    
            all_workers_h = docs.filtered(lambda x: x.category_ids.name in ('Worker'))
            all_staffs_h = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'Expatriate'))
            workercount_h = len(all_workers_h)
            staffcount_h = len(all_staffs_h)
              
    
            c_male_workers_h = all_workers_h.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_workers_h = all_workers_h.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_workers_h = all_workers_h.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_workers_h = all_workers_h.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_workers_cost_h = sum(c_male_workers_h.mapped('contract_id.wage'))
            c_female_workers_cost_h = sum(c_female_workers_h.mapped('contract_id.wage'))
            nc_male_workers_cost_h = sum(nc_male_workers_h.mapped('contract_id.wage'))
            nc_female_workers_cost_h = sum(nc_female_workers_h.mapped('contract_id.wage'))
    
            c_male_staff_cost_h = sum(c_male_staff_h.mapped('contract_id.wage'))
            c_female_staff_cost_h = sum(c_female_staff_h.mapped('contract_id.wage'))
            nc_male_staff_cost_h = sum(nc_male_staff_h.mapped('contract_id.wage'))
            nc_female_staff_cost_h = sum(nc_female_staff_h.mapped('contract_id.wage'))
            #worker
            w_wages_sum_h = sum([*c_male_workers_h.mapped('contract_id.wage'),*c_female_workers_h.mapped('contract_id.wage'),*nc_male_workers_h.mapped('contract_id.wage'),*nc_female_workers_h.mapped('contract_id.wage')])
            #staff
            s_wages_sum_h = sum([c_male_staff_cost_h,c_female_staff_cost_h,nc_male_staff_cost_h,nc_female_staff_cost_h])
            
    
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_h, column_product_style)
            worksheet.write(row, 2, 'HO SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_h, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_h, column_product_style)
            worksheet.write(row, 6, 'HO SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_h, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_h, report_small_title_style)
            row+=1
        else:
            all_workers = docs.filtered(lambda x: x.category_ids.name in ('Worker', 'Z-Worker', 'B-Worker', 'C-Zipper Worker', 'C-Button Worker', 'C-Worker'))
            all_staffs = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'B-Staff', 'Z-Staff', 'Z-Expatriate', 'Expatriate', 'B-Expatriate', 'C-Button Staff', 'C-Zipper Staff', 'C-Staff'))
            workercount = len(all_workers)
            staffcount = len(all_staffs)
            
            c_male_workers = all_workers.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_workers = all_workers.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_workers = all_workers.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_workers = all_workers.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_staff = all_staffs.filtered(lambda x: x.gender == 'male' and x.resign_date > x.probation_date)
            c_female_staff = all_staffs.filtered(lambda x: x.gender == 'female' and x.resign_date > x.probation_date)
            
            nc_male_staff = all_staffs.filtered(lambda x: x.gender == 'male' and x.resign_date <= x.probation_date)
            nc_female_staff = all_staffs.filtered(lambda x: x.gender == 'female' and x.resign_date <= x.probation_date)
    
            c_male_workers_cost = sum(c_male_workers.mapped('contract_id.wage'))
            c_female_workers_cost = sum(c_female_workers.mapped('contract_id.wage'))
            nc_male_workers_cost = sum(nc_male_workers.mapped('contract_id.wage'))
            nc_female_workers_cost = sum(nc_female_workers.mapped('contract_id.wage'))
    
            c_male_staff_cost = sum(c_male_staff.mapped('contract_id.wage'))
            c_female_staff_cost = sum(c_female_staff.mapped('contract_id.wage'))
            nc_male_staff_cost = sum(nc_male_staff.mapped('contract_id.wage'))
            nc_female_staff_cost = sum(nc_female_staff.mapped('contract_id.wage'))
            #worker
            w_wages_sum = sum([*c_male_workers.mapped('contract_id.wage'),*c_female_workers.mapped('contract_id.wage'),*nc_male_workers.mapped('contract_id.wage'),*nc_female_workers.mapped('contract_id.wage')])
            #staff
            s_wages_sum = sum([c_male_staff_cost,c_female_staff_cost,nc_male_staff_cost,nc_female_staff_cost])
            
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount, column_product_style)
            worksheet.write(row, 2, 'WORKER SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount, column_product_style)
            worksheet.write(row, 6, 'STAFF SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers), report_small_title_style)
            worksheet.write(row, 2, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff), report_small_title_style)
            worksheet.write(row, 6, 'Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers), report_small_title_style)
            worksheet.write(row, 2, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff), report_small_title_style)
            worksheet.write(row, 6, 'Non Confirmed - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost, report_small_title_style)
            row+=1
        



        
        # worksheet.merge_range(row, 1, row, 3, 'Objective / Score', merge_format_)
        # row=5
        
        # for line in report_data:
        #     col=0
        #     for l in line:
        #         worksheet.write(row, col, l, report_small_title_style)
        #         col+=1
        #     row+=1
        
        #worksheet.write(4, 0, 'SL.', column_product_style)
        #raise UserError((row+1))
        # worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        # worksheet.write(row, 5, round(grandtotal), report_small_title_style)
        #raise UserError((datefrom,dateto,bankname,categname))
        workbook.close()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Resign Employee')),
            'target': 'self',
        }    


    def joining_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
                 
        if data.get('date_from'):
            domain.append(('joining_date', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('joining_date', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43))) 

        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('company_id.id', 'in',(1,2,3)))
        com_all = data.get('company_all')
        
        domain.append(('active', '=', True))
        # datefrom = data.get('date_from')
        dateto = data.get('date_to')
        #raise UserError((domain))
        # docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)

        docs = self.env['hr.employee'].search(domain).sorted(key=lambda r: r.joining_date or '', reverse=False)
        
        # docs = docs.sorted(key = 'date_to', reverse=False)
        # docs1 = self.env['hr.contract'].search(domain).sorted(key = 'id', reverse=False)
        # docs1 = self.env['hr.employee.relation'].search(domain)
        #raise UserError((docs.id))
        datefrom = data.get('date_from')
        dateto = data.get('date_to')
        # bankname = self.bank_id.name
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
        # today = datetime.today().date()
        
        report_data = []
        emp_data = []
        slnumber=0
        for edata in docs:
            # today = datetime.today().date()
            # age = (data.get('date_to') - edata.birthday).days // 365 if edata.birthday else ''
            # status = ''
            # if edata.resign_date > edata.probation_date:
            #     status = 'CONFIRMED'
            # else:
            #     status = 'NOT CONFIRMED'
            if edata.birthday:
                age = int((data.get('date_to') - edata.birthday).days // 365)
            else:
                age = ''

            if edata.replacement_new:
                replacement = edata.replacement_new
            else:
                replacement = ''

            if edata.study_field:
                study = edata.study_field
            else:
                study = ''
                
            if edata.email:
                email = edata.email
            else:
                email = ''
          
            slnumber = slnumber+1
            emp_data = [
                slnumber,
                edata.emp_id,
                edata.name,
                edata.company_id.name,
                edata.category_ids.name,
                edata.department_id.parent_id.name,
                edata.department_id.name,
                edata.job_id.name,
                edata.grade,
                edata.joining_date,
                edata.gender,
                edata.birthday,
                age,
                edata.contract_id.wage,
                study,
                replacement,
                edata.marital,
                email,
                edata.mobile,
                # status,
            ]
            report_data.append(emp_data)     
    
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet(('Joining Employee'))

        report_title_style = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#714B62', 'font_color':'#FFFFFF'})
        report_title_style2 = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#343A40', 'font_color':'#FFFFFF'})
        report_title_style3 = workbook.add_format({'bold': True, 'font_size': 14, 'bg_color': '#343A40', 'font_color':'#FFFFFF', 'num_format': 'd-mmm-yy'})
        worksheet.merge_range('A1:S1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
        # worksheet.merge_range('A2:H2', 'Employee Joining Data', report_title_style2)
        worksheet.merge_range('A2:S2', 'Employee Joining Data - Total Employees: {}'.format(slnumber), report_title_style2)
        worksheet.merge_range('A3:S3', 'From: {} To: {}'.format(datefrom, dateto), report_title_style3)

        report_small_title_style = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        report_small_title_style2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 10, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': 'd-mmm-yy'})
#         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('I2:J2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style2)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
#         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        
        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})

        merge_format_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 12, 'font_color':'#FFFFFF'})
        merge_format_.set_text_wrap()

        worksheet.freeze_panes(3, 5)

        # set the width od the column
        
        worksheet.set_column(0, 0, 5)
        worksheet.set_column(1, 1, 7)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 4, 18)
        worksheet.set_column(5, 7, 26)
        worksheet.set_column(8, 8, 8)
        worksheet.set_column(9, 10, 12)
        worksheet.set_column(11, 11, 23)
        worksheet.set_column(12, 12, 8)
        worksheet.set_column(13, 13, 20)
        worksheet.set_column(14, 14, 25)
        worksheet.set_column(15, 16, 20)
        worksheet.set_column(17, 17, 30)
        worksheet.set_column(18, 18, 15)
        
        # worksheet.set_row(2, 20)
        
        
        worksheet.write(3, 0, 'SL.', column_product_style)
        worksheet.write(3, 1, 'ID', column_product_style)        
        worksheet.write(3, 2, 'Name', column_product_style)
        worksheet.write(3, 3, 'Unit', column_product_style)
        worksheet.write(3, 4, 'Category', column_product_style)
        worksheet.write(3, 5, 'Department', column_product_style)
        worksheet.write(3, 6, 'Section', column_product_style)
        worksheet.write(3, 7, 'Designation', column_product_style)
        worksheet.write(3, 8, 'Grade', column_product_style)
        worksheet.write(3, 9, 'Joining Date', column_product_style)
        worksheet.write(3, 10, 'Gender', column_product_style)
        worksheet.write(3, 11, 'Date of Birth', column_product_style)
        worksheet.write(3, 12, 'Age', column_product_style)
        worksheet.write(3, 13, 'Gross Salary', column_product_style)
        worksheet.write(3, 14, 'Academic Qualifications', column_product_style)
        worksheet.write(3, 15, 'Replacement / New Head', column_product_style)
        worksheet.write(3, 16, 'Marital Status', column_product_style)
        worksheet.write(3, 17, 'Email', column_product_style)
        worksheet.write(3, 18, 'Mobile Number', column_product_style)
        
        col = 0
        row=4
        
        # grandtotal = 0
        for line in report_data:
            col = 0
            # wei = None
            for l in line:
                if col == 9:
                    worksheet.write(row, col, l, report_small_title_style2)
                    col+=1
                elif col == 11:
                    worksheet.write(row, col, l, report_small_title_style2)
                    col+=1
                # elif col == 15 and (l == False):
                #     worksheet.write(row, col, '', report_small_title_style)
                #     col+=1
                # elif col == 15 and (l != ''):
                #     worksheet.write(row, col, l, report_small_title_style)
                #     col+=1
                elif (col in (0,1,2,3,4,5,6,7,8,10,12,13,14,15,16,17,18)):
                    worksheet.write(row, col, l, report_small_title_style)
                    col+=1
            row+=1

        worksheet.write(row, 1, row-4, column_issued_style)
        worksheet.write(row, 13, '=SUM(N{0}:N{1})'.format(5, row), column_issued_style)


        row+=2

        #allcompany == 
        if data.get('company_all'):
            # raise UserError (('hi'))

            all_workers = docs.filtered(lambda x: x.category_ids.name in ('Worker', 'Z-Worker', 'B-Worker', 'C-Zipper Worker', 'C-Button Worker', 'C-Worker'))
            all_staffs = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'B-Staff', 'Z-Staff', 'Z-Expatriate', 'Expatriate', 'B-Expatriate', 'C-Button Staff', 'C-Zipper Staff', 'C-Staff'))
            workercount = len(all_workers)
            staffcount = len(all_staffs)
            
            workerwage = sum(all_workers.mapped('contract_id.wage'))
            staffwage = sum(all_staffs.mapped('contract_id.wage'))
            #worker
            worksheet.write(row, 1, workercount, column_product_style)
            worksheet.write(row, 2, 'WORKERS SUMMARY', merge_format_)
            worksheet.write(row, 3, workerwage, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount, column_product_style)
            worksheet.write(row, 6, 'STAFF SUMMARY', merge_format_)
            worksheet.write(row, 7, staffwage, column_product_style)
            row+=1
    
     #Zipper      
            
    
            # # all_emp = docs.filtered(lambda x: x.category_ids.name in ('Worker', 'Z-Worker', 'B-Worker', 'C-Zipper Worker', 'C-Button Worker', 'C-Worker'))
            all_workers_z = docs.filtered(lambda x: x.category_ids.name in ('Z-Worker'))
            all_staffs_z = docs.filtered(lambda x: x.category_ids.name in ('Z-Staff', 'Z-Expatriate'))
            workercount_z = len(all_workers_z)
            staffcount_z = len(all_staffs_z)
              
    
            c_male_workers_z = all_workers_z.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_workers_z = all_workers_z.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_workers_z = all_workers_z.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_workers_z = all_workers_z.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_staff_z = all_staffs_z.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_workers_cost_z = sum(c_male_workers_z.mapped('contract_id.wage'))
            c_female_workers_cost_z = sum(c_female_workers_z.mapped('contract_id.wage'))
            nc_male_workers_cost_z = sum(nc_male_workers_z.mapped('contract_id.wage'))
            nc_female_workers_cost_z = sum(nc_female_workers_z.mapped('contract_id.wage'))
    
            c_male_staff_cost_z = sum(c_male_staff_z.mapped('contract_id.wage'))
            c_female_staff_cost_z = sum(c_female_staff_z.mapped('contract_id.wage'))
            nc_male_staff_cost_z = sum(nc_male_staff_z.mapped('contract_id.wage'))
            nc_female_staff_cost_z = sum(nc_female_staff_z.mapped('contract_id.wage'))
            #worker
            w_wages_sum_z = sum([*c_male_workers_z.mapped('contract_id.wage'),*c_female_workers_z.mapped('contract_id.wage'),*nc_male_workers_z.mapped('contract_id.wage'),*nc_female_workers_z.mapped('contract_id.wage')])
            #staff
            s_wages_sum_z = sum([c_male_staff_cost_z,c_female_staff_cost_z,nc_male_staff_cost_z,nc_female_staff_cost_z])
            #all
    
            #worker
    
            row+=1
    
            #worker
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_z, column_product_style)
            worksheet.write(row, 2, 'Zipper SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_z, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_z, column_product_style)
            worksheet.write(row, 6, 'Zipper SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_z, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_z, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_z), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_z, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_z), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_z, report_small_title_style)
            row+=1
    
    #metal Trims
    
            all_workers_m = docs.filtered(lambda x: x.category_ids.name in ('B-Worker'))
            all_staffs_m = docs.filtered(lambda x: x.category_ids.name in ('B-Staff','B-Expatriate'))
            workercount_m = len(all_workers_m)
            staffcount_m = len(all_staffs_m)
              
    
            c_male_workers_m = all_workers_m.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_workers_m = all_workers_m.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_workers_m = all_workers_m.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_workers_m = all_workers_m.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_staff_m = all_staffs_m.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_workers_cost_m = sum(c_male_workers_m.mapped('contract_id.wage'))
            c_female_workers_cost_m = sum(c_female_workers_m.mapped('contract_id.wage'))
            nc_male_workers_cost_m = sum(nc_male_workers_m.mapped('contract_id.wage'))
            nc_female_workers_cost_m = sum(nc_female_workers_m.mapped('contract_id.wage'))
    
            c_male_staff_cost_m = sum(c_male_staff_m.mapped('contract_id.wage'))
            c_female_staff_cost_m = sum(c_female_staff_m.mapped('contract_id.wage'))
            nc_male_staff_cost_m = sum(nc_male_staff_m.mapped('contract_id.wage'))
            nc_female_staff_cost_m = sum(nc_female_staff_m.mapped('contract_id.wage'))
            #worker
            w_wages_sum_m = sum([*c_male_workers_m.mapped('contract_id.wage'),*c_female_workers_m.mapped('contract_id.wage'),*nc_male_workers_m.mapped('contract_id.wage'),*nc_female_workers_m.mapped('contract_id.wage')])
            #staff
            s_wages_sum_m = sum([c_male_staff_cost_m,c_female_staff_cost_m,nc_male_staff_cost_m,nc_female_staff_cost_m])
    
            
            #worker
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_m, column_product_style)
            worksheet.write(row, 2, 'Metal Trims SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_m, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_m, column_product_style)
            worksheet.write(row, 6, 'Metal Trims SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_m, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_m, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_m), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_m, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_m), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_m, report_small_title_style)
            row+=1
    
    #Head Office
    
            all_workers_h = docs.filtered(lambda x: x.category_ids.name in ('Worker'))
            all_staffs_h = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'Expatriate'))
            workercount_h = len(all_workers_h)
            staffcount_h = len(all_staffs_h)
              
    
            c_male_workers_h = all_workers_h.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_workers_h = all_workers_h.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_workers_h = all_workers_h.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_workers_h = all_workers_h.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_staff_h = all_staffs_h.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_workers_cost_h = sum(c_male_workers_h.mapped('contract_id.wage'))
            c_female_workers_cost_h = sum(c_female_workers_h.mapped('contract_id.wage'))
            nc_male_workers_cost_h = sum(nc_male_workers_h.mapped('contract_id.wage'))
            nc_female_workers_cost_h = sum(nc_female_workers_h.mapped('contract_id.wage'))
    
            c_male_staff_cost_h = sum(c_male_staff_h.mapped('contract_id.wage'))
            c_female_staff_cost_h = sum(c_female_staff_h.mapped('contract_id.wage'))
            nc_male_staff_cost_h = sum(nc_male_staff_h.mapped('contract_id.wage'))
            nc_female_staff_cost_h = sum(nc_female_staff_h.mapped('contract_id.wage'))
            #worker
            w_wages_sum_h = sum([*c_male_workers_h.mapped('contract_id.wage'),*c_female_workers_h.mapped('contract_id.wage'),*nc_male_workers_h.mapped('contract_id.wage'),*nc_female_workers_h.mapped('contract_id.wage')])
            #staff
            s_wages_sum_h = sum([c_male_staff_cost_h,c_female_staff_cost_h,nc_male_staff_cost_h,nc_female_staff_cost_h])
    
            
            #worker
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount_h, column_product_style)
            worksheet.write(row, 2, 'HO SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum_h, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount_h, column_product_style)
            worksheet.write(row, 6, 'HO SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum_h, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost_h, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers_h), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost_h, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff_h), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost_h, report_small_title_style)
            row+=1
            
        else:
            all_workers = docs.filtered(lambda x: x.category_ids.name in ('Worker', 'Z-Worker', 'B-Worker', 'C-Zipper Worker', 'C-Button Worker', 'C-Worker'))
            all_staffs = docs.filtered(lambda x: x.category_ids.name in ('Staff', 'B-Staff', 'Z-Staff', 'Z-Expatriate', 'Expatriate', 'B-Expatriate', 'C-Button Staff', 'C-Zipper Staff', 'C-Staff'))
            workercount = len(all_workers)
            staffcount = len(all_staffs)
              
    
            c_male_workers = all_workers.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_workers = all_workers.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_workers = all_workers.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_workers = all_workers.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_staff = all_staffs.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'NEWHEAD')
            c_female_staff = all_staffs.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'NEWHEAD')
            
            nc_male_staff = all_staffs.filtered(lambda x: x.gender == 'male' and x.replacement_new == 'REPLACEMENT')
            nc_female_staff = all_staffs.filtered(lambda x: x.gender == 'female' and x.replacement_new == 'REPLACEMENT')
    
            c_male_workers_cost = sum(c_male_workers.mapped('contract_id.wage'))
            c_female_workers_cost = sum(c_female_workers.mapped('contract_id.wage'))
            nc_male_workers_cost = sum(nc_male_workers.mapped('contract_id.wage'))
            nc_female_workers_cost = sum(nc_female_workers.mapped('contract_id.wage'))
    
            c_male_staff_cost = sum(c_male_staff.mapped('contract_id.wage'))
            c_female_staff_cost = sum(c_female_staff.mapped('contract_id.wage'))
            nc_male_staff_cost = sum(nc_male_staff.mapped('contract_id.wage'))
            nc_female_staff_cost = sum(nc_female_staff.mapped('contract_id.wage'))
            #worker
            w_wages_sum = sum([*c_male_workers.mapped('contract_id.wage'),*c_female_workers.mapped('contract_id.wage'),*nc_male_workers.mapped('contract_id.wage'),*nc_female_workers.mapped('contract_id.wage')])
            #staff
            s_wages_sum = sum([c_male_staff_cost,c_female_staff_cost,nc_male_staff_cost,nc_female_staff_cost])
            #all
            
    
            #worker
            worksheet.write(row, 1, 'No. of Head')
            worksheet.write(row, 3,'Salary Cost')
            #staff
            worksheet.write(row, 5, 'No. of Head')
            worksheet.write(row, 7,'Salary Cost')
            row+=1
            #worker
            worksheet.write(row, 1, workercount, column_product_style)
            worksheet.write(row, 2, 'WORKERS SUMMARY', merge_format_)
            worksheet.write(row, 3, w_wages_sum, column_product_style)
            #staff
            worksheet.write(row, 5, staffcount, column_product_style)
            worksheet.write(row, 6, 'STAFF SUMMARY', merge_format_)
            worksheet.write(row, 7, s_wages_sum, column_product_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_male_workers), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 3, c_male_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_male_staff), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Male', report_small_title_style)
            worksheet.write(row, 7, c_male_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(c_female_workers), report_small_title_style)
            worksheet.write(row, 2, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 3, c_female_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(c_female_staff), report_small_title_style)
            worksheet.write(row, 6, 'New Head - Female', report_small_title_style)
            worksheet.write(row, 7, c_female_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_male_workers), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 3, nc_male_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_male_staff), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Male', report_small_title_style)
            worksheet.write(row, 7, nc_male_staff_cost, report_small_title_style)
            row+=1
            #worker
            worksheet.write(row, 1, len(nc_female_workers), report_small_title_style)
            worksheet.write(row, 2, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 3, nc_female_workers_cost, report_small_title_style)
            #staff
            worksheet.write(row, 5, len(nc_female_staff), report_small_title_style)
            worksheet.write(row, 6, 'Replacement Head - Female', report_small_title_style)
            worksheet.write(row, 7, nc_female_staff_cost, report_small_title_style)
            row+=1
        
            

        
        # for line in report_data:
        #     col=0
        #     for l in line:
        #         worksheet.write(row, col, l, report_small_title_style)
        #         col+=1
        #     row+=1
        
        #worksheet.write(4, 0, 'SL.', column_product_style)
        #raise UserError((row+1))
        # worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        # worksheet.write(row, 5, round(grandtotal), report_small_title_style)
        #raise UserError((datefrom,dateto,bankname,categname))
        workbook.close()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Joining Employee')),
            'target': 'self',
        }    

  



class HRISReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.hris_employee_profile_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }
class HRISReportPDF2(models.AbstractModel):
    _name = 'report.taps_hr.hris_joining_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))       
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
#         raise UserError((docs.ids))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%d-%m-%Y'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }          

class HRISReportPDF3(models.AbstractModel):
    _name = 'report.taps_hr.hris_appointment_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
#         raise UserError((docs.ids))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        } 
    
class HRISReportPDF4(models.AbstractModel):
    _name = 'report.taps_hr.hris_confirmation_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
       
        # c_date = docs.joining_date +  relativedelta(months=+6)
        # raise UserError((c_date))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
            # 'c_date' : c_date,
#             'alldays': all_datelist
        }


class HRISReportPDF5(models.AbstractModel):
    _name = 'report.taps_hr.hris_trail_extension_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
#         raise UserError((docs.ids))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }
    
class HRISReportPDF6(models.AbstractModel):
    _name = 'report.taps_hr.hris_training_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
#         raise UserError((docs.ids))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }
    
class HRISReportPDF7(models.AbstractModel):
    _name = 'report.taps_hr.hris_no_dues_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
#         raise UserError((docs.ids))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }
    
class HRISReportPDF8(models.AbstractModel):
    _name = 'report.taps_hr.hris_loan_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))        
         
            
        domain.append(('active', 'in',(False,True)))
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%d-%m-%Y'),
            data.get('date_to'),
            
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }

class ACopeningReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.acopening_pdf_template'
    _description = 'AC opening Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))        
         
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        domains=[]
        if data.get('bank_id'):
            domains.append(('id', '=', data.get('bank_id')))
        bank = self.env['res.bank'].search(domains)
        
        #raise UserError((domains))
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            datetime.datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%d %b, %Y'),
            data.get('date_to'),
            bank.name,
        ]
        common_data.append(common_data)
        # raise UserError((common_data[4]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
            'bank' : bank.name
#             
        }
    
    
class BirthCalenderReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.hris_birth_calendar_pdf_template'
    _description = 'Birth Calender Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        
        query = """ """
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        #if data.get('date_from'):
            #domain.append(('date_from', '>=', data.get('date_from')))
        #if data.get('date_to'):
            #domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
         
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        #raise UserError((docs.id))
        emplist = docs.mapped('id')
        em_list = '0'
        for e in emplist:
            em_list = em_list + ',' + str(e)
        #dfsdfj = datetime.datetime.now()
        birth_month = data.get('date_from')
        birth_month = birth_month[5:7]
        b_m = int(birth_month)

        query = """ select emp_id, name, to_char(birthday,'DD Month YYYY') AS birth_date, cast((AGE(current_date,birthday)) as varchar) as age_, mobile_phone, work_email from hr_employee where id in (""" + em_list + """) and EXTRACT(MONTH FROM birthday)=%s and 1=%s order by birth_date ASC """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, (b_m, 1))
        birthday = cursor.fetchall()
        allemp_data = []
        for details in docs:            
            emp_data = []
            emp_data = [
                data.get('date_from'),
                data.get('date_to'),
                details.id,
                details.emp_id,
                details.name,
                details.department_id.parent_id.name,
                details.department_id.name,
                details.job_id.name,
                
            ]
            allemp_data.append(emp_data)
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%B-%Y'),
        ]
        common_data.append(common_data)
        
        emp = docs.sorted(key = 'id')[:1]
        
        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
        #raise UserError((docs.ids))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': allemp_data,
            'cd' : common_data,
            'birth': birthday,
            'category' : heading_type,
#             
        }
    
class AnniversaryCalenderReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.hris_anniversary_calendar_pdf_template'
    _description = 'Anniversary Calender Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        
        query = """ """
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        #if data.get('date_from'):
            #domain.append(('date_from', '>=', data.get('date_from')))
        #if data.get('date_to'):
            #domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))        
         
            
        domain.append(('active', 'in',(False,True)))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        #raise UserError((docs.id))
        emplist = docs.mapped('id')
        em_list = '0'
        for e in emplist:
            em_list = em_list + ',' + str(e)
        #dfsdfj = datetime.datetime.now()
        marriage_month = data.get('date_from')
        marriage_month = marriage_month[5:7]
        m_m = int(marriage_month)
        
        
        #raise UserError((em_list))
        query = """ select emp_id, name, to_char("marriage_date",'DD Month YYYY') AS marriage_date, cast((date_part('year', current_date))-(date_part('year', "marriage_date")) as varchar) as marriage_age_, mobile_phone, work_email from hr_employee where id in (""" + em_list + """) and EXTRACT(MONTH FROM "marriage_date")=%s and 1=%s order by marriage_date ASC """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query, (m_m, 1))
        marriageday = cursor.fetchall()
        allemp_data = []
        for details in docs:           
            emp_data = []
            emp_data = [
                data.get('date_from'),
                data.get('date_to'),
                details.id,
                details.emp_id,
                details.name,
                details.department_id.parent_id.name,
                details.department_id.name,
                details.job_id.name,
                
            ]
            allemp_data.append(emp_data)
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%B-%Y'),
            
        ]
        common_data.append(common_data)
        
        emp = docs.sorted(key = 'id')[:1]
        
        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
        #raise UserError((docs.ids))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': allemp_data,
            'cd' : common_data,
            'marriage': marriageday,
            'category' : heading_type,
#             
        }
    
class PfReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.hris_pf_pdf_template'
    _description = 'Monthly PF Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        
        query = """ """
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        #if data.get('date_from'):
            #domain.append(('date_from', '>=', data.get('date_from')))
        #if data.get('date_to'):
            #domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))        
         
            
        domain.append(('active', 'in',(False,True)))
        domain.append(('contribution_sum', '!=', 0))
        
        
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        #raise UserError((docs.id))
        emplist = docs.mapped('id')
        em_list = '0'
        for e in emplist:
            em_list = em_list + ',' + str(e)
        
        #raise UserError((em_list))
        query = """ select employee_id, year, to_char(salary_month, 'Month') AS month_, pf_amount,0 as basic_wage,salary_month
from provident_fund_line where employee_id in (""" + em_list + """)
union
select employee_id,cast(DATE_PART('year',date_to) as varchar) as year,to_char(date(date_to), 'Month') AS month_,pf_empe_wage as pf_amount,basic_wage, date(date_to) as salary_month
from hr_payslip where  employee_id in (""" + em_list + """) and pf_empe_wage>0 order by salary_month; """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query)
        pf = cursor.fetchall()
        allemp_data = []
        for details in docs:            
            emp_data = []
            emp_data = [
                data.get('date_from'),
                data.get('date_to'),
                details.id,
                details.emp_id,
                details.name,
                details.department_id.parent_id.name,
                details.department_id.name,
                details.job_id.name,
                details.joining_date,
                details.service_length,
                details.grade,
                details.contract_id.wage,
                details.contract_id.pf_activationDate,
                
            ]
            allemp_data.append(emp_data)
        
        common_data=[]
        common_data = [
            data.get('report_type'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%B-%Y'),
            
        ]
        common_data.append(common_data)
        
        emp = docs.sorted(key = 'id')[:1]
        
        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
        #raise UserError((docs.ids))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': allemp_data,
            'cd' : common_data,
            'pf': pf,
            'category' : heading_type,
#             
        }  

class HRISReportPDF9(models.AbstractModel):
    _name = 'report.taps_hr.hris_mariage_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))            
            
        domain.append(('active', 'in',(False,True)))
        
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
#             otTotal,
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }

    
class HRISReportPDF10(models.AbstractModel):
    _name = 'report.taps_hr.hris_pf_loan_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))        
         
            
        domain.append(('active', 'in',(False,True)))
           
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)       
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%d-%m-%Y'),
            data.get('date_to'),
            
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }    

class HRISReportPDF11(models.AbstractModel):
    _name = 'report.taps_hr.hris_retention_risk_matrix_pdf_template'
    _description = 'HRIS Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('bank_account_id.bank_id', '=', data.get('bank_id')))
        if data.get('employee_type'):
            if data.get('employee_type')=='staff':
                domain.append(('category_ids.id', 'in',(15,21,31)))
            if data.get('employee_type')=='expatriate':
                domain.append(('category_ids.id', 'in',(16,22,32)))
            if data.get('employee_type')=='worker':
                domain.append(('category_ids.id', 'in',(20,30)))
            if data.get('employee_type')=='cstaff':
                domain.append(('category_ids.id', 'in',(26,44,47)))
            if data.get('employee_type')=='cworker':
                domain.append(('category_ids.id', 'in',(25,42,43)))
            
        domain.append(('active', 'in',(False,True)))
        
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        common_data=[]    
        common_data = [
            data.get('report_type'),
            datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%d-%m-%Y'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        
        emp = docs.sorted(key = 'id')[:1]
        # count = 0
        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
            # raise UserError((heading_type))
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
        if data.get('employee_type'):
            heading_type = emp.category_ids.name
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
            'category' : heading_type,
        }