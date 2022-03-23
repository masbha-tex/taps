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

class EmployeeCardPDFReport(models.TransientModel):
    _name = 'employee.profile.card.pdf.report'
    _description = 'Employee Profile'#access_employee_card_pdf_report,access_employee_card_pdf_report,model_employee_profile_card_pdf_report,base.group_user,1,1,1,1 

    date_from = fields.Date('Date from', required=True, default = date.today().strftime('2000-%m-01'))
    date_to = fields.Date('Date to', required=True, default = date.today())
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Mode', required=True, default='employee',
        help='By Employee: Request for individual Employee, By Employee Tag: Request for group of employees in category')
    
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
        for profile in self:
            if profile.employee_id:
                profile.department_id = profile.employee_id.department_id
            elif profile.mode_type == 'department':
                if not profile.department_id:
                    profile.department_id = self.env.user.employee_id.department_id
            else:
                profile.department_id = False
                
    #@api.depends('mode_type')
    def _compute_from_mode_type(self):
        for profile in self:
            if profile.mode_type == 'employee':
                if not profile.employee_id:
                    profile.employee_id = self.env.user.employee_id
                profile.mode_company_id = False
                profile.category_id = False
                profile.department_id = False
            elif profile.mode_type == 'company':
                if not profile.mode_company_id:
                    profile.mode_company_id = self.env.company.id
                profile.category_id = False
                profile.department_id = False
                profile.employee_id = False
            elif profile.mode_type == 'department':
                if not profile.department_id:
                    profile.department_id = self.env.user.employee_id.department_id
                profile.employee_id = False
                profile.mode_company_id = False
                profile.category_id = False
            elif profile.mode_type == 'category':
                if not profile.category_id:
                    profile.category_id = self.env.user.employee_id.category_ids
                profile.employee_id = False
                profile.mode_company_id = False
                profile.department_id = False
                
    # generate PDF report
    def action_print_report(self):
        if self.mode_type == "employee":#employee  company department category
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': False, 'category_id': False, 'employee_id': self.employee_id.id}
        if self.mode_type == "company":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': self.mode_company_id.id, 'department_id': False, 'category_id': False, 'employee_id': False}
        if self.mode_type == "department":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': self.department_id.id, 'category_id': False, 'employee_id': False}
        if self.mode_type == "category":
            data = {'date_from': self.date_from, 'date_to': self.date_to, 'mode_company_id': False, 'department_id': False, 'category_id': self.category_id.id, 'employee_id': False}
        #raise UserError(('efewfewf'))
        return self.env.ref('taps_hr.action_employee_card_pdf_report').report_action(self, data=data)

#     Generate xlsx report
#     def action_generate_xlsx_report(self):
#         data = {
#             'date_from': self.date_from,
#             'date_to': self.date_to,
#         }
#         return self.env.ref('taps_hr.action_openacademy_xlsx_report').report_action(self, data=data)
    
    
class EmployeeCardReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.employee_card_pdf_template'
    _description = 'Employee Profile Template'
    

    def _get_report_values(self, docids, data=None):
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
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        
        
        #raise UserError((domain))    
        docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.employee',
            'docs': docs,
        }

    
