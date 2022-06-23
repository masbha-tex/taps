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

class SalarySheet(models.TransientModel):
    _name = 'salary.sheet.pdf.report'
    _description = 'Salary Sheet'      

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('PAYSLIP',	'Pay Slip'),
        ('SALARYTOP',	'Salary Top Sheet Summary'),
        ('SALARY',	'Salary Sheet'),
        ('BONUSTOP',	'Bonus Top Sheet Summary'),
        ('BONUS',	'Bonus Sheet'),],
        string='Report Type', required=True, default='PAYSLIP',
        help='By Payroll Report')
    
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('companyall', 'By All Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED')],
        string='All Company', required=False)     
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
    employee_id = fields.Many2one(
        'hr.employee',  string='Employee', index=True, readonly=False, ondelete="restrict")    
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)
    
    employee_type = fields.Selection([
        ('staf', 'Stafs'),
        ('worker', 'Workers'),
        ('expatriate', 'Expatriates'),
        ('cstaf', 'C-Stafs'),
        ('cworker', 'C-workers')],
        string='Employee Type', required=False)    
    
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
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}
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
                        'is_company': self.is_company}              
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
                        'is_company': self.is_company}                
        if self.report_type == 'PAYSLIP':
            return self.env.ref('taps_hr.action_pay_slip_pdf_report').report_action(self, data=data)
        if self.report_type == 'SALARYTOP':
            return self.env.ref('taps_hr.action_top_sheet_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'SALARY':
            return self.env.ref('taps_hr.action_salary_sheet_pdf_report').report_action(self, data=data)
        if self.report_type == 'BONUSTOP':
            return self.env.ref('taps_hr.action_bonus_top_sheet_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'BONUS':
            return self.env.ref('taps_hr.action_bonus_sheet_pdf_report').report_action(self, data=data)

class PaySlipReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.pay_slip_pdf_template'
    _description = 'Pay Slip Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("pay_slip_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
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
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }    

class SalaryTopSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.top_sheet_pdf_template'
    _description = 'Salary Top Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("top_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
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
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }
    
class SalarySheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.salary_sheet_pdf_template'
    _description = 'Salary Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("salary_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
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
        
        
        #raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        #raise UserError((emplist)) ,department_id.parent_id.id,department_id.id
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        allemp_data = []
        dept_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                i = 0
                for r in allemp_data:
                    if (allemp_data[i][0] == details.company_id.id) and (allemp_data[i][2] == details.department_id.parent_id.id) and (allemp_data[i][4] == details.department_id.id):
                        i = i+1
                        add = False
                        break
                    else:
                        i = i+1
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name # Section Name
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        
        add = True
        j = 0
        for dep in allemp_data:
            emp_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (dept_data[i][0] == details.company_id.id) and (dept_data[i][2] == details.department_id.parent_id.id):
                        i = i+1
                        add = False
                        break
                    else:
                        i = i+1
            if add == True:
                emp_data = [
                    allemp_data[j][0],#company id
                    allemp_data[j][2],#department id
                    allemp_data[j][3] #department name
                ]
                dept_data.append(emp_data)
            add = True
            j = j+1
        
       
        
        
#         flag_datelist = []
#         flag_dates = []
#         #raise UserError((docs.id)) 
#         delta = flag_enddate - flag_stdate
#         for i in range(delta.days + 1):
#             day = stdate + timedelta(days=i)
#             flag_dates = [
#                 day,
#             ]
#             flag_datelist.append(flag_dates)
        

    
            

            
            
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
#        raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': allemp_data,
#            'datas': common_data,
#             'alldays': all_datelist,
            'dpt': dept_data,
            'sec': section,
            'com': company,
#             'stdate': stdate_data,
#             'lsdate': lsdate_data,
            'is_com' : data.get('is_company')
        }
    
class BonusTopSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.bonus_top_sheet_pdf_template'
    _description = 'Bonus Top Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("bonus_top_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
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
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }
    
class BonusSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.bonus_sheet_pdf_template'
    _description = 'Bonus Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("bonus_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
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
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }
    
