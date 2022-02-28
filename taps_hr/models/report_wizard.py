from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
import re

class JobCardPDFReport(models.TransientModel):
    _name = 'job.card.pdf.report'

    date_from = fields.Date('Date from', required=True, default = datetime.now())
    date_to = fields.Date('Date to', required=True, default = datetime.now())
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    
    
    employee_id = fields.Many2one(
        'hr.employee',  string='Employee', index=True, readonly=False, ondelete="restrict", tracking=True)
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False, tracking=True)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False, tracking=True)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False, tracking=True)
    
    
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
    def action_generate_xlsx_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
        }
        return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)

class OpenAcademyPDFReport(models.TransientModel):
    _name = 'openacademy.pdf.report'

    date_from = fields.Date('Date from', required=True)
    date_to = fields.Date('Date to', required=True)
    course_ids = fields.Many2many('openacademy.course', string='Course')
    responsible_id = fields.Many2one('res.users', 'Responsible')

    # generate PDF report
    def action_print_report(self):
        data = {'date_from': self.date_from, 'date_to': self.date_to, 'course_ids': self.course_ids.ids, 'responsible_id': self.responsible_id.id}
        return self.env.ref('taps_hr.action_openacademy_pdf_report').report_action(self, data=data)

    # Generate xlsx report
    def action_generate_xlsx_report(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'course_ids': self.course_ids.ids,
            'responsible_id': self.responsible_id.id
        }
        return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)


class OpenAcademyReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.openacademy_pdf_template'

    def _get_report_values(self, docids, data=None):
        domain = [('state', '!=', 'cancel')]
        if data.get('date_from'):
            domain.append(('course_date', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('course_date', '<=', data.get('date_to')))
        if data.get('course_ids'):
            domain.append(('id', 'in', data.get('course_ids')))
        if data.get('responsible_id'):
            domain.append(('responsible_id', '=', data.get('responsible_id')))
        docs = self.env['openacademy.course'].search(domain)
        responsible = self.env['res.users'].browse(data.get('responsible_id'))
        course_ids = self.env['openacademy.course'].browse(data.get('course_ids'))
        data.update({'responsbile': responsible.name})
        data.update({'courses': ",".join([course.course_name for course in course_ids])})
        return {
            'doc_ids': docs.ids,
            'doc_model': 'openacademy.course',
            'docs': docs,
            'datas': data
        }

class JobCardReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.jobcard_pdf_template'
    
            #    if not holiday.mode_company_id:
            #        holiday.mode_company_id = self.env.company.id
            #    holiday.category_id = False
            #    holiday.department_id = False
            #    holiday.employee_id = False
            #elif holiday.holiday_type == 'departme

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
        
        
        #raise UserError((domain))    
        docs = self.env['hr.attendance'].search(domain).sorted(key = 'attDate', reverse=False)
        
        #responsible = self.env['res.users'].browse(data.get('responsible_id'))
        #course_ids = self.env['openacademy.course'].browse(data.get('course_ids'))
        #data.update({'responsbile': responsible.name})
        #data.update({'courses': ",".join([course.course_name for course in course_ids])})
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': data
        }