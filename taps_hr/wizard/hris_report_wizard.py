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
        ('retentionincentive',	'Retention Incentive'),],
        string='Report Type', required=True, default='employee_profile',
        help='By HRIS Report')
    
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
    
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)     
    
    file_data = fields.Binary(readonly=True, attachment=False)   

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