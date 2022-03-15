import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from datetime import timedelta
import re
import math

class Attreprocess(models.TransientModel):
    _name = 'att.reprocess'
    _description = 'Attendance Reprocess'      

    date_from = fields.Date('Date from', required=True, 
                            default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_by = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Report Mode', required=True, default='employee')
    
    employee_id = fields.Many2one(
        'hr.employee',  string='Employee', index=True, readonly=False, ondelete="restrict")    
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)
    
    
    file_data = fields.Binary(readonly=True, attachment=False)    
    
    @api.depends('employee_id', 'report_by')
    def _compute_department_id(self):
        for holiday in self:
            if holiday.employee_id:
                holiday.department_id = holiday.employee_id.department_id
            elif holiday.report_by == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
            else:
                holiday.department_id = False
                
    #@api.depends('report_by')
    def _compute_from_report_by(self):
        for holiday in self:
            if holiday.report_by == 'employee':
                if not holiday.employee_id:
                    holiday.employee_id = self.env.user.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.department_id = False
            elif holiday.report_by == 'company':
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                holiday.category_id = False
                holiday.department_id = False
                holiday.employee_id = False
            elif holiday.report_by == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.report_by == 'category':
                if not holiday.category_id:
                    holiday.category_id = self.env.user.employee_id.category_ids
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.department_id = False
            #else:
            #    holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
    # generate PDF report
    def action_att_reprocess(self):
        if self.report_by == "employee":#employee  company department category
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': self.employee_id.id}

        if self.report_by == "company":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': self.mode_company_id.id, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': False}

        if self.report_by == "department":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': self.department_id.id, 
                    'category_id': False, 
                    'employee_id': False}

        if self.report_by == "category":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': self.category_id.id, 
                    'employee_id': False}
#         raise UserError(('domain'))        
        #return self.env.ref('taps_hr.report_salary_sheet').report_action(self, data=data)
        domain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        
        
        emp_att = self.env['hr.attendance'].search(domain)#.sorted(key = 'employee_id', reverse=False)
        
        if emp_att:
            for record in emp_att:
                if record.check_in == False:
                    record[-1].write({'check_in': '2032-01-01 02:02:30','check_out': '2032-01-01 02:02:44'})
                    record[-1].write({'check_in': '','check_out': ''})
                else:
                    if record.check_out == False:
                        record[-1].write({'check_out': '2032-01-01 02:02:50'})
                        record[-1].write({'check_out': ''})
                    else:
                        record[-1].write({'check_out': record.check_out + timedelta(seconds=1)})
                        record[-1].write({'check_out': record.check_out - timedelta(seconds=1)})
        
