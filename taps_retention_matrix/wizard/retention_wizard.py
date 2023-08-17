# import base64
# import io
# import logging
# from odoo import models, fields, api
# from datetime import datetime, date, timedelta, time
# import datetime
# from dateutil.relativedelta import relativedelta
# from odoo.exceptions import UserError, ValidationError
# from odoo.tools.misc import xlsxwriter
# from odoo.tools import format_date, format_datetime
# import re
# import math

# _logger = logging.getLogger(__name__)

# class RetentionPDFReport(models.TransientModel):
#     _name = 'hris.pdf.report'
#     _description = 'Retention Report'    

#     date_from = fields.Date('Date from', default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
#     date_to = fields.Date('Date to', default = fields.Date.today().strftime('%Y-%m-25'))
#     report_type = fields.Selection([

#         ('retentionmatrix', 'Retention Risk Matrix'),],
#         string='Report Type', required=True, default='employee_profile',
#         help='By Retention Report')
    
#     mode_type = fields.Selection([
#         ('employee', 'By Employee'),
#         ('company', 'By Company'),
#         ('department', 'By Department'),
#         ('category', 'By Employee Tag'),
#         ('emptype', 'By Employee Type')],
#         string='Mode Type', required=True, default='employee',
#         help='By Employee: Report for individual Employee, By Employee Tag: Report for group of employees in category')
    
    
#     bank_id = fields.Many2one(
#         'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
#     employee_id = fields.Many2one(
#         'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
#     category_id = fields.Many2one(
#         'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
#     mode_company_id = fields.Many2one(
#         'res.company',  string='Company Mode', readonly=False)
#     department_id = fields.Many2one(
#         'hr.department',  string='Department', readonly=False)
    
#     employee_type = fields.Selection([
#         ('staff', 'Staffs'),
#         ('worker', 'Workers'),
#         ('expatriate', 'Expatriates'),
#         ('cstaff', 'C-Staffs'),
#         ('cworker', 'C-workers')],
#         string='Employee Type', required=False)
    
#     types = fields.Selection([
#         ('morning', 'Morning Shift'),
#         ('evening', 'Evening Shift'),
#         ('night', 'Night Shift')
#     ], string='Shift Type', index=True, store=True, copy=True)     
    
#     file_data = fields.Binary(readonly=True, attachment=False)    
    
#     @api.depends('employee_id', 'mode_type')
#     def _compute_department_id(self):
#         for hris in self:
#             if hris.employee_id:
#                 hris.department_id = hris.employee_id.department_id
#             elif hris.mode_type == 'department':
#                 if not hris.department_id:
#                     hris.department_id = self.env.user.employee_id.department_id
#             else:
#                 hris.department_id = False
                
#     #@api.depends('mode_type')
#     def _compute_from_mode_type(self):
#         for hris in self:
#             if hris.mode_type == 'employee':
#                 if not hris.employee_id:
#                     hris.employee_id = self.env.user.employee_id
#                 hris.mode_company_id = False
#                 hris.category_id = False
#                 hris.department_id = False
#             elif hris.mode_type == 'company':
#                 if not hris.mode_company_id:
#                     hris.mode_company_id = self.env.company.id
#                 hris.category_id = False
#                 hris.department_id = False
#                 hris.employee_id = False
#             elif hris.mode_type == 'department':
#                 if not hris.department_id:
#                     hris.department_id = self.env.user.employee_id.department_id
#                 hris.employee_id = False
#                 hris.mode_company_id = False
#                 hris.category_id = False
#             elif hris.mode_type == 'category':
#                 if not hris.category_id:
#                     hris.category_id = self.env.user.employee_id.category_ids
#                 hris.employee_id = False
#                 hris.mode_company_id = False
#                 hris.department_id = False
#             #else:
#             #    hris.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
#     # generate PDF report
#     def action_print_report(self):
#         if self.report_type:
#             if self.mode_type == "employee":#employee  company department category
#                 #raise UserError((self.report_type))
#                 data = {'date_from': self.date_from, 
#                         'date_to': self.date_to, 
#                         'mode_company_id': False, 
#                         'department_id': False, 
#                         'category_id': False, 
#                         'employee_id': self.employee_id.id,
#                         'report_type': self.report_type,
#                         'bank_id': self.bank_id.id,
#                         'types': self.types,
#                         'employee_type': self.employee_type}

#             if self.mode_type == "company":
#                 data = {'date_from': self.date_from, 
#                         'date_to': self.date_to, 
#                         'mode_company_id': self.mode_company_id.id, 
#                         'department_id': False, 
#                         'category_id': False, 
#                         'employee_id': False, 
#                         'report_type': self.report_type,
#                         'bank_id': self.bank_id.id,
#                         'types': self.types,
#                         'employee_type': self.employee_type}

#             if self.mode_type == "department":
#                 data = {'date_from': self.date_from, 
#                         'date_to': self.date_to, 
#                         'mode_company_id': False, 
#                         'department_id': self.department_id.id, 
#                         'category_id': False, 
#                         'employee_id': False, 
#                         'report_type': self.report_type,
#                         'bank_id': self.bank_id.id,
#                         'types': self.types,
#                         'employee_type': self.employee_type}

#             if self.mode_type == "category":
#                 data = {'date_from': self.date_from, 
#                         'date_to': self.date_to, 
#                         'mode_company_id': False, 
#                         'department_id': False, 
#                         'category_id': self.category_id.id, 
#                         'employee_id': False, 
#                         'report_type': self.report_type,
#                         'bank_id': self.bank_id.id,
#                         'types': self.types,
#                         'employee_type': self.employee_type}
#             if self.mode_type == "emptype":
#                 data = {'date_from': self.date_from, 
#                         'date_to': self.date_to, 
#                         'mode_company_id': False, 
#                         'department_id': False, 
#                         'category_id': False, 
#                         'employee_id': False, 
#                         'report_type': self.report_type,
#                         'bank_id': self.bank_id.id,
#                         'types': self.types,
#                         'employee_type': self.employee_type}                
       
#         if self.report_type == 'retentionmatrix':
#             return self.env.ref('taps_hr.action_hris_retention_risk_matrix_pdf_report').report_action(self, data=data)



# class HRISReportPDF11(models.AbstractModel):
#     _name = 'report.taps_hr.hris_retention_risk_matrix_pdf_template'
#     _description = 'HRIS Report Template'     

#     def _get_report_values(self, docids, data=None):
#         domain = []
        
# #         if data.get('bank_id')==False:
# #             domain.append(('code', '=', data.get('report_type')))
# #         if data.get('date_from'):
# #             domain.append(('date_from', '>=', data.get('date_from')))
# #         if data.get('date_to'):
# #             domain.append(('date_to', '<=', data.get('date_to')))
#         if data.get('mode_company_id'):
#             #str = re.sub("[^0-9]","",data.get('mode_company_id'))
#             domain.append(('company_id.id', '=', data.get('mode_company_id')))
#         if data.get('department_id'):
#             #str = re.sub("[^0-9]","",data.get('department_id'))
#             domain.append(('department_id.id', '=', data.get('department_id')))
#         if data.get('category_id'):
#             #str = re.sub("[^0-9]","",data.get('category_id'))
#             domain.append(('category_ids.id', '=', data.get('category_id')))
#         if data.get('employee_id'):
#             #str = re.sub("[^0-9]","",data.get('employee_id'))
#             domain.append(('id', '=', data.get('employee_id')))
#         # if data.get('bank_id'):
#         #     #str = re.sub("[^0-9]","",data.get('employee_id'))
#         #     domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
#         if data.get('employee_type'):
#             if data.get('employee_type')=='staff':
#                 domain.append(('category_ids.id', 'in',(15,21,31)))
#             if data.get('employee_type')=='expatriate':
#                 domain.append(('category_ids.id', 'in',(16,22,32)))
#             if data.get('employee_type')=='worker':
#                 domain.append(('category_ids.id', 'in',(20,30)))
#             if data.get('employee_type')=='cstaff':
#                 domain.append(('category_ids.id', 'in',(26,44,47)))
#             if data.get('employee_type')=='cworker':
#                 domain.append(('category_ids.id', 'in',(25,42,43)))


        
            
#         domain.append(('active', 'in',(False,True)))
#         docs = self.env['hr.employee'].search(domain).sorted(key = 'id', reverse=False)
        
        
        
        

        
#         common_data=[]    
#         common_data = [
#             data.get('report_type'),
            
# #             otTotal,
#             datetime.datetime.strptime(data.get('date_from'), '%Y-%m-%d').strftime('%d-%m-%Y'),
#             data.get('date_to'),
#         ]
#         common_data.append(common_data)
        
#         emp = docs.sorted(key = 'id')[:1]
#         # count = 0
#         if data.get('mode_company_id'):
#             heading_type = emp.company_id.name
#             # raise UserError((heading_type))
#         if data.get('department_id'):
#             heading_type = emp.department_id.name
#         if data.get('category_id'):
#             heading_type = emp.category_ids.name
#         if data.get('employee_id'):
#             heading_type = emp.name
#         if data.get('employee_type'):
#             heading_type = emp.category_ids.name
        
#         return {
#             'doc_ids': docs.ids,
#             'doc_model': 'hr.employee',
#             'docs': docs,
#             'category' : heading_type,
            
            
            
# #             'alldays': all_datelist
#         }