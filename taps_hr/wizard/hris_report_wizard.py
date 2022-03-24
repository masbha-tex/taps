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

class HRISPDFReport(models.TransientModel):
    _name = 'hris.pdf.report'
    _description = 'HRIS Report'    

    date_from = fields.Date('Date from', default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('employee_profile',	'Employee Profile'),
        ('joining',	'Joining Letter'),        
        ('appointment',	'Appointment Letter'),
        ('confirmation',	'Confirmation Letter'),
        ('trail_extension',	'Extension of Probation Period'),
        ('no_dues',	'No Dues Certificate'),
        ('pf',	'Monthly PF Statement'),
        ('loan',	'Loan Application'),
        ('marriage',	'Marriage Certificate'),
#         ('appraisal',	'Performance Appraisal'),
        ('shift',	'Weekly Shift Schedule'),
        ('attcalendar',	'Attendance Calendar'),
        ('training',	'Worker Training Program'), 
        ('birthcalendar',	'Birthday Calendar'),
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
                        'bank_id': False}

            if self.mode_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False}

            if self.mode_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False}

            if self.mode_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False}
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
        if self.report_type == 'marriage':
            return self.env.ref('taps_hr.action_hris_marriage_pdf_report').report_action(self, data=data)
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
        
        
           
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
    
    
