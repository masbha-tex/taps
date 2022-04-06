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

class AttendancePDFReport(models.TransientModel):
    _name = 'attendance.pdf.report'
    _description = 'Attendace Report'     

    date_from = fields.Date('Date from', required=True, default=(date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('job_card',	'Employee Job Card'),
        ('dailyatten',	'Daily Attendance'),        
        ('dailyatten_ot',	'Daily Attendance OT'),
        ('dailyatten_ots',	'Daily Attendance with OT'),
        ('daily_manpower',	'Daily Manpower Summary'),
        ('ac_opening',	'Account Opening Letter'),
        ('head_count',	'Head Count Report'),
        ('payroll_planning', 'Payroll Planning Report'),
        ('monthly_manhours', 'Monthly Manhours Report'),
        ('daily_manhours',	'Daily Manhours Report'),
        ('daily_ot_analysis',	'Daily OT Analysis'),
        ('daily_atten_summary',	'Daily Attendance Summary'), 
        ('monthly_atten_summary',	'Monthly Attendance Summary'),
        ('holiday_slip',	'Off Day/Holiday Duty Slip'),
        ('daily_excess_ot',	'Daily Excess OT'),
        ('daily_salary_cost',	'Daily Salary Cost'),],
        string='Report Type', required=True, default='job_card',
        help='By Attendance Reporting')
    atten_type = fields.Selection([
        ('p',	'Present'),
        ('l',	'Late'),
        ('a',	'Absent'),
        ('fp',	'Friday Present'),
        ('hp',	'Holiday Present'),
        ('eo',	'Early Out'),
        ('po',	'Pending Out'),
        ('cl',	'Casual Time Off'),
        ('sl',	'Seek Time Off'),
        ('el', 'Earn Time off'),
        ('ml', 'Metarnity Time off'),
        ('lw',	'Leave without pay'),
        ('co',	'C-Off'),
        ('aj',	'Adjustment Days'),],
        string='Attendance Type', required=False, #default='p',
        help='By Attendance Reporting')
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Attendance Reporting for individual Employee, By Employee Tag: Attendance Reporting for group of employees in category')
    
    
    
    employee_id = fields.Many2one(
        'hr.employee',  string='Employee', index=True, readonly=False, ondelete="restrict")
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)
    
    
    @api.depends('employee_id', 'mode_type')
    def _compute_department_id(self):
        for atten in self:
            if atten.employee_id:
                atten.department_id = atten.employee_id.department_id
            elif atten.mode_type == 'department':
                if not atten.department_id:
                    atten.department_id = self.env.user.employee_id.department_id
            else:
                atten.department_id = False
                
    #@api.depends('mode_type')
    def _compute_from_mode_type(self):
        for atten in self:
            if atten.mode_type == 'employee':
                if not atten.employee_id:
                    atten.employee_id = self.env.user.employee_id
                atten.mode_company_id = False
                atten.category_id = False
                atten.department_id = False
            elif atten.mode_type == 'company':
                if not atten.mode_company_id:
                    atten.mode_company_id = self.env.company.id
                atten.category_id = False
                atten.department_id = False
                atten.employee_id = False
            elif atten.mode_type == 'department':
                if not atten.department_id:
                    atten.department_id = self.env.user.employee_id.department_id
                atten.employee_id = False
                atten.mode_company_id = False
                atten.category_id = False
            elif atten.mode_type == 'category':
                if not atten.category_id:
                    atten.category_id = self.env.user.employee_id.category_ids
                atten.employee_id = False
                atten.mode_company_id = False
                atten.department_id = False
                
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
                        'atten_type': self.atten_type}

            if self.mode_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type}

            if self.mode_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type}

            if self.mode_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type}
        if self.report_type == 'job_card':
            return self.env.ref('taps_hr.action_job_pdf_report').report_action(self, data=data)
        if self.report_type == 'dailyatten':
            return self.env.ref('taps_hr.action_dailyatten_pdf_report').report_action(self, data=data)
        if self.report_type == 'dailyatten_ot':
            return self.env.ref('taps_hr.action_dailyatten_ot_pdf_report').report_action(self, data=data)
        if self.report_type == 'dailyatten_ots':
            return self.env.ref('taps_hr.action_dailyatten_ots_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_manpower':
            return self.env.ref('taps_hr.action_daily_manpower_pdf_report').report_action(self, data=data)
        if self.report_type == 'ac_opening':
            return self.env.ref('taps_hr.action_ac_opening_pdf_report').report_action(self, data=data)
        if self.report_type == 'head_count':
            return self.env.ref('taps_hr.action_head_count_pdf_report').report_action(self, data=data)
        if self.report_type == 'payroll_planning':
            return self.env.ref('taps_hr.action_payroll_planning_pdf_report').report_action(self, data=data)
        if self.report_type == 'monthly_manhours':
            return self.env.ref('taps_hr.action_monthly_manhours_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_manhours':
            return self.env.ref('taps_hr.action_daily_manhours_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_ot_analysis':
            return self.env.ref('taps_hr.action_daily_ot_analysis_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_atten_summary':
            return self.env.ref('taps_hr.action_daily_atten_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'monthly_atten_summary':
            return self.env.ref('taps_hr.action_monthly_atten_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'holiday_slip':
            return self.env.ref('taps_hr.action_holiday_slip_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_excess_ot':
            return self.env.ref('taps_hr.action_daily_excess_ot_pdf_report').report_action(self, data=data)
        if self.report_type == 'daily_salary_cost':
            return self.env.ref('taps_hr.action_daily_salary_cost_pdf_report').report_action(self, data=data)
    
    

    # Generate xlsx report
#     def action_generate_xlsx_report(self):
#         data = {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#         }
#         return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)
    
    
class JobReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.job_pdf_template'
    _description = 'Job Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))            
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
    
class DailyattenReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.dailyatten_pdf_template'
    _description = 'Dailyatten Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailyattenotReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.dailyattenot_pdf_template'
    _description = 'Dailyattenot Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))       
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailyattenotsReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.dailyattenots_pdf_template'
    _description = 'Dailyattenots Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailymanpowerReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.dailymanpower_pdf_template'
    _description = 'Dailymanpower Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class ACopeningReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.acopening_pdf_template'
    _description = 'AC opening Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class HeadcountReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.head_count_pdf_template'
    _description = 'Head count Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class PayrollplanningReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.payroll_planning_pdf_template'
    _description = 'Payroll planning Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class MonthlymanhoursReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.monthly_manhours_pdf_template'
    _description = 'Monthly Manhours Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailymanhoursReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.daily_manhours_pdf_template'
    _description = 'Daily Manhours Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailyotanalysisReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.daily_ot_analysis_pdf_template'
    _description = 'AC opening Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))        
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailyattensummaryReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.daily_atten_summary_pdf_template'
    _description = 'Daily atten summary Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))        
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class MonthlyattensummaryReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.monthly_atten_summary_pdf_template'
    _description = 'Monthlyattensummary Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))        
        
        #department_id,parent_id,hr_department
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class HolidayslipReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.holiday_slip_pdf_template'
    _description = 'Holidayslip Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        if data.get('atten_type'):
            if data.get('atten_type')=='p':
                domain.append(('inFlag', '=', 'P'))
            if data.get('atten_type')=='l':
                domain.append(('inFlag', '=', 'L'))
            if data.get('atten_type')=='a':
                domain.append(('inFlag', '=', 'A'))
            if data.get('atten_type')=='fp':
                domain.append(('inFlag', '=', 'FP'))
            if data.get('atten_type')=='hp':
                domain.append(('inFlag', '=', 'HP'))
            if data.get('atten_type')=='eo':
                domain.append(('outFlag', '=', 'EO'))
            if data.get('atten_type')=='po':
                domain.append(('outFlag', '=', 'PO'))
            if data.get('atten_type')=='cl':
                domain.append(('inFlag', '=', 'CL'))
            if data.get('atten_type')=='sl':
                domain.append(('inFlag', '=', 'SL'))
            if data.get('atten_type')=='el':
                domain.append(('inFlag', '=', 'EL'))
            if data.get('atten_type')=='ml':
                domain.append(('inFlag', '=', 'ML'))
            if data.get('atten_type')=='lw':
                domain.append(('inFlag', '=', 'LW'))
            if data.get('atten_type')=='co':
                domain.append(('inFlag', '=', 'CO'))
            if data.get('atten_type')=='aj':
                domain.append(('inFlag', '=', 'AJ'))        
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailyexcessotReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.daily_excess_ot_pdf_template'
    _description = 'Dailyexcessot Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
class DailysalarycostReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.daily_salary_cost_pdf_template'
    _description = 'Dailysalarycost Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
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
        
        #domain.append(('employee_id.active', '=', True))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
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
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        } 

    
