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
from dateutil.relativedelta import relativedelta
_logger = logging.getLogger(__name__)

class AttendancePDFReport(models.TransientModel):
    _name = 'attendance.pdf.report'
    _description = 'Attendace Report'     

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    report_type = fields.Selection([
        ('job_card',	'Employee Job Card'),
        ('dailyatten',	'Daily Attendance'),        
        ('dailyatten_ot',	'Daily Attendance OT'),
        ('dailyatten_ots',	'Daily Attendance with OT'),
        ('daily_manpower',	'Daily Manpower Summary'),
        ('head_count',	'Head Count Report'),
        ('payroll_planning', 'Payroll Planning Report'),
        ('monthly_manhours', 'Monthly Manhours Report'),
        ('daily_manhours',	'Daily Manhours Report'),
        ('daily_ot_analysis',	'Daily OT Analysis'),
        ('daily_atten_summary',	'Daily Attendance Summary'), 
        ('monthly_atten_summary',	'Monthly Attendance Summary'),
        ('holiday_slip',	'Off Day/Holiday Duty Slip'),
        ('daily_excess_ot',	'Daily Excess OT'),
        ('daily_salary_cost',	'Daily Salary Cost'),
        ('atten_calender',	'Attendance Calender'),
        ('shift_schedule',       'Shift Schedule')],
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
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)    
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Attendance Reporting for individual Employee, By Employee Tag: Attendance Reporting for group of employees in category')
    
    
    
    employee_id = fields.Many2one(
        'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)

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
                        'atten_type': self.atten_type,
                        'types': self.types,
                        'is_company': self.is_company}

            if self.mode_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type,
                        'types': self.types,
                        'is_company': self.is_company}

            if self.mode_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type,
                        'types': self.types,
                        'is_company': self.is_company}

            if self.mode_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'atten_type': self.atten_type,
                        'types': self.types,
                        'is_company': self.is_company}
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
        if self.report_type == 'atten_calender':
            return self.env.ref('taps_hr.action_atten_calender_pdf_report').report_action(self, data=data)
        if self.report_type == 'shift_schedule':
            return self.env.ref('taps_hr.action_shift_schedule_pdf_report').report_action(self, data=data)
            
 
    
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
                
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist)), ('active', 'in',(False,True))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id))
        delta = enddate - stdate
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
#         raise UserError((docs.id)) 
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
        lstmonths_data = []
        stdate_data = []
        lsdate_data = []
        heading_type = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                details.contract_id.basic,
                details.shift_group.types,
                details.shift_group.graceinTime,
                
            ]
            allemp_data.append(emp_data)

        stdate_data = []
        stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
        ]
        stdate_data.append(stdate_data)

        lsdat_data = []
        lsdat_data = [

            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

        ]
        lsdate_data.append(lsdat_data)

        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name  
            
        #raise UserError((section.id,department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category':heading_type,
            'is_com' : data.get('is_company')
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
#         raise UserError((docs.id)) 
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
        lstmonths_data = []
        stdate_data = []
        lsdate_data = []
        heading_type = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                details.contract_id.basic,
            ]
            allemp_data.append(emp_data)

        stdate_data = []
        stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
        ]
        stdate_data.append(stdate_data)

        lsdat_data = []
        lsdat_data = [

            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

        ]
        lsdate_data.append(lsdat_data)

        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name  
            
        #raise UserError((section.id,department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category':heading_type,
            'is_com' : data.get('is_company')
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
        
        
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        #raise UserError((department.id)) 
        
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
        lstmonths_data = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                duty_hour,
            ]
            allemp_data.append(emp_data)
            
            
#             stdate_data = []
#             stdate_data = [
#                 datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
                

                
#             ]
#             stdate_data.append(stdate_data)
            
            lstmonth_data = []
            lstmonth_data = [
                datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B  %Y'),

                
            ]
            lstmonths_data.append(lstmonth_data)
            
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
            
        #raise UserError((section.id, allemp_data[0][9],department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'month': lstmonths_data,
            'category': heading_type,
            'is_com' : data.get('is_company')
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
        lstmonths_data = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                duty_hour,
            ]
            allemp_data.append(emp_data)
            
            
            stdate_data = []
            stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
            ]
            stdate_data.append(stdate_data)
            
            lsdate_data = []
            lsdate_data = [
                
                datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

            ]
            lsdate_data.append(lsdate_data)
            
            
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name
            
        #raise UserError((section.id, allemp_data[0][9],department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category': heading_type,
            'is_com' : data.get('is_company')
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
        
        
#         raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
#         raise UserError((docs.id)) 
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
        lstmonths_data = []
        stdate_data = []
        lsdate_data = []
        heading_type = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                details.contract_id.basic,
            ]
            allemp_data.append(emp_data)

        stdate_data = []
        stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
        ]
        stdate_data.append(stdate_data)

        lsdat_data = []
        lsdat_data = [

            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

        ]
        lsdate_data.append(lsdat_data)

        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name            
        #raise UserError((section.id, allemp_data[0][9],department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category':heading_type,
            'is_com' : data.get('is_company')
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
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
        lstmonths_data = []
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
                details.department_id.id,
            ]
            allemp_data.append(emp_data)
            
            
            lstmonth_data = []
            lstmonth_data = [
                datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B  %Y'),

                
            ]
            lstmonths_data.append(lstmonth_data)
        #raise UserError((section.id, allemp_data[0][9],department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'month': lstmonths_data,
            'is_com' : data.get('is_company')
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
                details.joining_date,
                details.service_length,
                details.grade,
                details.category_ids.name,
                details.contract_id.isActivePF,
                
                
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'is_com' : data.get('is_company')
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
#         raise UserError((docs.id)) 
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
        lstmonths_data = []
        stdate_data = []
        lsdate_data = []
        heading_type = []
        for details in employee:
            otTotal = 0
            duty_hour = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    duty_hour = abs(de.outTime-de.inTime)
            
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
                details.department_id.id,
                details.joining_date,
                details.contract_id.basic,
                
                
            ]
            allemp_data.append(emp_data)

        stdate_data = []
        stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
        ]
        stdate_data.append(stdate_data)

        lsdat_data = []
        lsdat_data = [

            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

        ]
        lsdate_data.append(lsdat_data)

        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name  
            
        #raise UserError((section.id,department.id,section.parent_id.id))    
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category':heading_type,
            'is_com' : data.get('is_company')
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))

        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        stdate = fst_days.attDate
        enddate = lst_days.attDate

#         get_date = stdate
#         getdate = get_date
#         if getdate.day>=26:
#             flag_stdate = datetime.strptime(getdate.strftime('%Y-%m-26'), '%Y-%m-%d')
#             flag_enddate = datetime.strptime((getdate + relativedelta(months = 1)).strftime('%Y-%m-25'), '%Y-%m-%d')
            
#         else:
#             flag_stdate = datetime.strptime((getdate - relativedelta(months = 1)).strftime('%Y-%m-26'), '%Y-%m-%d')
#             flag_enddate = datetime.strptime(getdate.strftime('%Y-%m-25'), '%Y-%m-%d')
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        
        
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
                details.department_id.id,
                details.contract_id.wage,
                details.contract_id.basic
               
            ]
            allemp_data.append(emp_data)
            
            
            stdate_data = []
            stdate_data = [
                datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime("%b %d, %Y"),
               
            ]
            stdate_data.append(stdate_data)
            
            lsdate_data = []
            lsdate_data = [
                
                datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%b %d, %Y'),

            ]
            lsdate_data.append(lsdate_data)
            
            
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
            
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'alldays': all_datelist,
            'dpt': department,
            'sec': section,
            'stdate': stdate_data,
            'lsdate': lsdate_data,
            'category': heading_type,
            'is_com' : data.get('is_company')
            
            
        } 
    
class AttendanceCalenderReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.atten_calender_pdf_template'
    _description = 'Attendance Calender'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        domain_ = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
            domain_.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
            domain_.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
            domain_.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.id', '=', data.get('employee_id')))
            domain_.append(('employee_id.id', '=', data.get('employee_id')))
        
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
        employee_leave = self.env['hr.leave.report'].search([('employee_id', 'in', (emplist))])
        #raise UserError((employee_leave.id)) 
        fst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.search([('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to'))]).sorted(key = 'attDate', reverse=True)[:1]
        
        
        prev_date = fields.datetime.strptime(data.get('date_from'), '%Y-%m-%d')
        last_date = fields.datetime.strptime(data.get('date_to'), '%Y-%m-%d')
        a_date = data.get('date_from')
        a_date = a_date[8:10]
        a_d = int(a_date)

        if (a_d > 26) :
            prev_date = prev_date.replace(day= 26).strftime('%Y-%m-%d')
            last_date = (last_date+ timedelta(days=10)).strftime('%Y-%m-25')
        if (a_d <= 26) :
            prev_date = (prev_date.replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
            last_date = last_date.strftime('%Y-%m-25')
        
        att_docs = self.env['hr.attendance'].search(domain_).sorted(key = 'attDate', reverse=False)
        att_fst_days = att_docs.search([('attDate', '>=', prev_date),('attDate', '<=', last_date)]).sorted(key = 'attDate', reverse=False)[:1]
        att_lst_days = att_docs.search([('attDate', '>=', prev_date),('attDate', '<=', last_date)]).sorted(key = 'attDate', reverse=True)[:1]
        
        
#         prev_date = fields.datetime.strptime(data.get('date_from'), '%Y-%m-%d')
        
        
        
        
        
    
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        att_stdate = att_fst_days.attDate
        att_enddate = att_lst_days.attDate
        #raise UserError((att_fst_days.attDate)) 
        
        all_att_datelist = []
        att_dates = []
        #raise UserError((docs.id)) 
        att_delta = att_enddate - att_stdate       # as timedelta
        for i in range(att_delta.days + 1):
            day = att_stdate + timedelta(days=i)
            att_dates = [
                day,
            ]
            all_att_datelist.append(att_dates)
            
            
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
            
        all_datelist_ = []
        dates_ = []
        #raise UserError((docs.id)) 
        delta_ = fields.datetime.strptime(last_date,'%Y-%m-%d') - fields.datetime.strptime(prev_date, '%Y-%m-%d')      # as timedelta
        for i in range(delta_.days + 1):
            day =fields.datetime.strptime(prev_date, '%Y-%m-%d').date()   + timedelta(days=i)
            dates_ = [
                day,
            ]
            all_datelist_.append(dates_)
        

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
                details.joining_date,
                details.service_length,
                details.grade,
                details.contract_id.wage,
                details.contract_id.pf_activationDate,
                
            ]
            allemp_data.append(emp_data)
            
            
            em_list = '0'
        for e in emplist:
            em_list = em_list + ',' + str(e)
            
        query = """ select r.employee_id,t.name,r.number_of_days,
COALESCE((select sum(av.number_of_days) from hr_leave_report as av where av.holiday_status_id=r.holiday_status_id and av.employee_id=r.employee_id and av.leave_type='request' and av.state='validate'),0)
from hr_leave_report as r inner join hr_leave_type as t on r.holiday_status_id=t.id where r.employee_id in (""" + em_list + """) and r.leave_type='allocation' and r.state='validate'; """
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query)
        atten_calendar = cursor.fetchall()
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'att_docs' : att_docs,
            'datas': allemp_data,
            'alldays': all_datelist,
            'alldays_' : all_datelist_,
            'allattdays' : all_att_datelist,
            'is_com' : data.get('is_company'),
            'a_y' : fields.datetime.strptime(data.get('date_from'), '%Y-%m-%d'),
            'a_c' : atten_calendar
            
            
        }   
    
class ShiftScheduleReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.shift_schedule_pdf_template'
    _description = 'ShiftSchedule Template'      
    
    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('date_from'):
            domain.append(('activationDate', '>=', data.get('date_from')))
            
        if data.get('date_to'):
            domain.append(('activationDate', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('name.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('name.department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('name.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            
            domain.append(('name', '=', data.get('employee_id')))
        if data.get('types'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            
            domain.append(('transferGroup.types', '=', data.get('types')))
            
        
        docs = self.env['shift.transfer'].search(domain).sorted(key = 'activationDate', reverse=False)
        grouplist = docs.mapped('transferGroup.id')
        transfergroup = self.env['shift.setup'].search([('id', 'in', (grouplist))])

        emplist = docs.mapped('name.id')
        
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        
        
#         fst_days = docs.search([('activationDate', '>=', data.get('date_from')),('activationDate', '<=', data.get('date_to'))]).sorted(key = 'activationDate', reverse=False)[:1]
#         lst_days = docs.search([('activationDate', '>=', data.get('date_from')),('activationDate', '<=', data.get('date_to'))]).sorted(key = 'activationDate', reverse=True)[:1]
        
        sectionlist = employee.mapped('department_id.id')
        
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
#         stdate = fst_days.activationDate
#         #raise UserError((stdate))
#         enddate = lst_days.activationDate
        
#         all_datelist = []
#         dates = []
#         #raise UserError((docs.id)) 
#         delta = enddate - stdate       # as timedelta
#         for i in range(delta.days + 1):
#             day = stdate + timedelta(days=i)
#             dates = [
#                 day,
#             ]
#             all_datelist.append(dates)
        

        allemp_data = []
        lstmonths_data = []
        for details in employee:
#             otTotal = 0
#             for de in docs:
#                 if details.id == de.name.id:
#                     otTotal = otTotal + de.otHours
            
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
#                 otTotal,
                details.department_id.id,
            ]
            allemp_data.append(emp_data)
            
            
            lstmonth_data = []
            lstmonth_data = [
                datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B  %Y'),

                
            ]
            lstmonths_data.append(lstmonth_data)
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'dpt': department,
            'sec': section,
            'month': lstmonths_data,
            'shiftgroup': transfergroup,
            'is_com' : data.get('is_company')
        }