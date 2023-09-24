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

    report_type = fields.Selection([
        ('retentionmatrix', 'Retention Matrix'),],
        string='Report Type', required=True, default='retentionmatrix',
        help='By Retention Matrix Report')
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        # ('emptype', 'By Employee Category'),
        ('empgroup', 'By Employee Group')],
        string='Mode Type', required=True, default='employee',
        help='By Employee: Report for individual Employee, By Employee Tag: Report for group of employees in category')
    
    employee_id = fields.Many2one(
        'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department', domain="[('parent_id', '=', False)]", string='Department', readonly=False)
    
    employee_type = fields.Selection([
        ('staff', 'Staffs'),
        ('worker', 'Workers'),
        ('expatriate', 'Expatriates')],
        string='Employee Category', readonly=False)
    employee_group = fields.Many2one('hr.employee.group', string="Employee Group", readonly=False)    

    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(),  store=True, required=True)
    month = fields.Selection('_get_month_list', 'Month', default=lambda self: self._get_default_month(), store=True, required=True)     
    
    file_data = fields.Binary(readonly=True, attachment=False)

    @staticmethod
    def _get_year_list():
        current_year = datetime.date.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 2):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((next_year, year_label))
        return year_options

    @staticmethod
    def _get_default_year():
        current_year = datetime.date.today().year
        return str(current_year+1)

    @staticmethod
    def _get_month_list():
        current_year = datetime.date.today().year
        months = []
    
        # Generate labels for all months in the current year
        for month in range(1, 13):
            month_label = datetime.date(current_year, month, 1).strftime('%B')
            months.append((str(month), month_label))
    
        return months
    
    @staticmethod
    def _get_default_month():
        current_month = datetime.date.today().month
        return str(current_month)         
    
    def action_print_report(self):
        if self.report_type:
            if self.mode_type == "employee":
                data = {'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id,
                        'report_type': self.report_type,
                        'year': self.year,
                        'month': self.month,
                        'employee_type': self.employee_type,
                        'employee_group': False}

            if self.mode_type == "company":
                data = {'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'year': self.year,
                        'month': self.month,
                        'employee_type': self.employee_type,
                        'employee_group': False}

            if self.mode_type == "department":
                data = {'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'year': self.year,
                        'month': self.month,
                        'employee_type': self.employee_type,
                        'employee_group': False}

            if self.mode_type == "category":
                data = {'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'year': self.year,
                        'month': self.month,
                        'employee_type': self.employee_type,
                        'employee_group': False}
            # if self.mode_type == "emptype":
            #     data = {'mode_company_id': False, 
            #             'department_id': False, 
            #             'category_id': False, 
            #             'employee_id': False, 
            #             'report_type': self.report_type,
            #             'year': self.year,
            #             'month': self.month,
            #             'employee_type': self.employee_type,
            #             'employee_group': False} 
            if self.mode_type == "empgroup":
                data = {'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'year': self.year,
                        'month': self.month,
                        'employee_type': self.employee_type,
                        'employee_group': self.employee_group}                 
        if self.report_type == 'retentionmatrix':
            return self.env.ref('taps_retention_matrix.action_retention_matrix_pdf_report').report_action(self, data=data)



class RetentionReportPDF(models.AbstractModel):
    _name = 'report.taps_retention_matrix.retention_matrix_pdf_template'
    _description = 'Retention Matrix Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('mode_company_id'):
            domain.append(('company_id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('department_id.parent_id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id', '=', data.get('employee_id')))
        if data.get('employee_type'):
            domain.append(('category', '=', data.get('employee_type')))
        if data.get('employee_group'):
            domain.append(('employee_group', '=', data.get('employee_group')))            
        if data.get('year'):
            domain.append(('year', '=', data.get('year')))
        if data.get('month'):
            domain.append(('month', '=', data.get('month')))            
            
                        
        # domain.append(('active', 'in',(False,True)))
        # raise UserError((domain))
        
        docs = self.env['retention.matrix'].search(domain).sorted(key = 'id', reverse=False)
        
        common_data=[]    
        common_data = [
            data.get('report_type'),
        ]
        common_data.append(common_data)
        
        emp = docs.sorted(key = 'id')[:1]
        # count = 0
        if data.get('mode_company_id'):
            heading_type = emp.employee_id.company_id.name
            months = int(emp.month)
            if data.get('employee_type'):
                category = emp.category
            else:
                category = 'All'                
        if data.get('department_id'):
            heading_type = emp.employee_id.department_id.parent_id.name
            months = int(emp.month)
            if data.get('employee_type'):
                category = emp.category
            else:
                category = 'All'
        if data.get('category_id'):
            heading_type = emp.employee_id.category_ids.name
            months = int(emp.month)
            if data.get('employee_type'):
                category = emp.category
            else:
                category = 'All'         
        if data.get('employee_id'):
            heading_type = emp.employee_id.display_name
            months = int(emp.month)
            if data.get('employee_type'):
                category = emp.category
            else:
                category = 'All'         

        if data.get('employee_group'):
            heading_type = emp.employee_id.employee_group.name
            months = int(emp.month)
            if data.get('employee_type'):
                category = emp.category
            else:
                category = 'All'      

        
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'retention.matrix',
            'docs': docs,
            'category' : heading_type,
            'months' : months,
            'type' : category,
        }
        
    
