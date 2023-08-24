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
import re
import math

_logger = logging.getLogger(__name__)

class RetentionPDFReport(models.TransientModel):
    _name = 'retention.matrix.pdf.report'
    _description = 'Retention Report'    

    date_from = fields.Date('Date from', default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('retentionmatrix', 'Retention Matrix'),],
        string='Report Type', required=True, default='retentionmatrix',
        help='By Retention Matrix Report')
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
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
    quarter = fields.Selection(selection=[
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4'),], string="Quarter", index=True, store=True, copy=True, default='q1')

    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(),  store=True, required=True)
    
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)     
    
    file_data = fields.Binary(readonly=True, attachment=False)

    @api.depends('employee_id', 'mode_type')
    def _compute_department_id(self):
        for retention in self:
            if retention.employee_id:
                retention.department_id = retention.employee_id.department_id
            elif retention.mode_type == 'department':
                if not retention.department_id:
                    retention.department_id = self.env.user.employee_id.department_id
            else:
                retention.department_id = False

    def _compute_from_mode_type(self):
        for retention in self:
            if retention.mode_type == 'employee':
                if not retention.employee_id:
                    retention.employee_id = self.env.user.employee_id
                retention.mode_company_id = False
                retention.category_id = False
                retention.department_id = False
            elif retention.mode_type == 'company':
                if not retention.mode_company_id:
                    retention.mode_company_id = self.env.company.id
                retention.category_id = False
                retention.department_id = False
                retention.employee_id = False
            elif retention.mode_type == 'department':
                if not retention.department_id:
                    retention.department_id = self.env.user.employee_id.department_id
                retention.employee_id = False
                retention.mode_company_id = False
                retention.category_id = False
            elif retention.mode_type == 'category':
                if not retention.category_id:
                    retention.category_id = self.env.user.employee_id.category_ids
                retention.employee_id = False
                retention.mode_company_id = False
                retention.department_id = False

    @staticmethod
    def _get_year_list():
        current_year = datetime.date.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 1):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((next_year, year_label))
        return year_options

    @staticmethod
    def _get_default_year():
        current_year = datetime.date.today().year
        return str(current_year+1)
    
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
                        'year': self.year,
                        'types': self.types,
                        'quarter': self.quarter,
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
                        'year': self.year,
                        'types': self.types,
                        'quarter': self.quarter,
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
                        'year': self.year,
                        'types': self.types,
                        'quarter': self.quarter,
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
                        'year': self.year,
                        'types': self.types,
                        'quarter': self.quarter,
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
                        'year': self.year,
                        'types': self.types,
                        'quarter': self.quarter,
                        'employee_type': self.employee_type}                
        if self.report_type == 'retentionmatrix':
            return self.env.ref('taps_retention_matrix.action_retention_matrix_pdf_report').report_action(self, data=data)



class RetentionReportPDF(models.AbstractModel):
    _name = 'report.taps_retention_matrix.retention_matrix_pdf_template'
    _description = 'Retention Matrix Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []

        if data.get('quarter'):
            if data.get('quarter') == 'q1':
                domain.append(('year', '=', data.get('year')))
                domain.append(('quarter', '=', 'q1'))
            elif data.get('quarter') == 'q2':
                domain.append(('year', '=', data.get('year')))
                domain.append(('quarter', '=', 'q2'))
            elif data.get('quarter') == 'q3':
                domain.append(('year', '=', data.get('year')))
                domain.append(('quarter', '=', 'q3'))
            elif data.get('quarter') == 'q4':
                domain.append(('year', '=', data.get('year')))
                domain.append(('quarter', '=', 'q4'))
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('company_id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id', '=', data.get('employee_id')))
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
            
        # domain.append(('active', 'in',(False,True)))
        # raise UserError((domain))
        
        docs = self.env['retention.matrix'].search(domain).sorted(key = 'id', reverse=False)
        
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
            heading_type = emp.employee_id.company_id.name
            heading = emp.quarter
            # raise UserError((heading_type))
        if data.get('department_id'):
            heading_type = emp.employee_id.department_id.name
        if data.get('category_id'):
            heading_type = emp.employee_id.category_ids.name
            heading = emp.quarter
        if data.get('employee_id'):
            heading_type = emp.employee_id.display_name
            heading = emp.quarter
        if data.get('employee_type'):
            heading_type = emp.employee_id.category_ids.name
            heading = emp.quarter

        
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'retention.matrix',
            'docs': docs,
            'category' : heading_type,
            'qname' : heading,
        }
        
    
