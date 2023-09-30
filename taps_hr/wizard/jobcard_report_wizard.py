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

class JobCardPDFReport(models.TransientModel):
    _name = 'job.card.pdf.report'
    _description = 'Employee Job Card' #access_job_card_pdf_report,access_job_card_pdf_report,model_job_card_pdf_report,base.group_user,1,1,1,1     

    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    
    
    
    employee_id = fields.Many2one(
        'hr.employee',  domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employee', index=True, readonly=False, ondelete="restrict")
    
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
                
    # generate PDF report
    def action_print_report(self):
        if self.holiday_type == "employee":#employee  company department category
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': False, 'category_id': False, 'employee_id': self.employee_id.id}
        if self.holiday_type == "company":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': self.mode_company_id.id, 'department_id': False, 'category_id': False, 'employee_id': False}
        if self.holiday_type == "department":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': self.department_id.id, 'category_id': False, 'employee_id': False}
        if self.holiday_type == "category":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': False, 'category_id': self.category_id.id, 'employee_id': False}
        return self.env.ref('taps_hr.action_job_card_pdf_report').report_action(self, data=data)

    # Generate xlsx report
#     def action_generate_xlsx_report(self):
#         data = {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#         }
#         return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)
    
    
class JobCardReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.jobcard_pdf_template'
    _description = 'Employee Job Card Template'      
    
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

    
