import base64
import io
import logging
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError, Warning
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta
import re
import math
import xlsxwriter
_logger = logging.getLogger(__name__)

class SalarySheet(models.TransientModel):
    _name = 'salary.sheet.pdf.report'
    _description = 'Salary Sheet'      

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    report_type = fields.Selection([
        ('PAYSLIP',	'Pay Slip'),
        ('fnf',	'Full & Final Settlement'),
        ('SALARYTOP',	'Salary Top Sheet Summary'),
        ('SALARY',	'Salary Sheet'),
        ('BONUSTOP',	'Bonus Top Sheet Summary'),
        ('BONUS',	'Bonus Sheet'),
        ('increment',	'Increment & Promotion Letter'),],
        string='Report Type', required=True, default='PAYSLIP',
        help='By Payroll Report')
    
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('employees', 'By Employees'),
        ('company', 'By Company'),
        ('companyall', 'By All Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type'),],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED')],
        string='All Company', required=False)     
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
    employee_id = fields.Many2many(
        'hr.employee',  domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employees', index=True, readonly=False, ondelete="restrict")
    
    employee_ids = fields.Many2one(
        'hr.employee', domain="['|', ('active', '=', False), ('active', '=', True)]",  string='Employee', index=True, readonly=False, ondelete="restrict")
    
    # employee_id = fields.Many2many(comodel_name='hr.employee', relation='all_employee_list',column1='id',column2='name', domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employee', readonly=False, ondelete="restrict")
    
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

    employee_list = fields.Char(string="Emp List") 

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

    # @api.onchange('employee_id')
    # def _onchange_employee_id(self):
    #     empl = self.employee_id
    #     emp = empl.mapped('id')
    #     # raise UserError((self.employee_id))
    #     self.employee_list = emp
        # invalid_partners = self.employee_id#.filtered(lambda partner: not partner.private_email)
        # if invalid_partners:
        #     warning = {
        #         'title': 'Invalid "Employee" Email',
        #         'message': (("%s do not have emails. please set the emails from employee!") % invalid_partners.display_name),
        #     }
        #     self.employee_id -= invalid_partners
        #     return {'warning': warning}
                
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
        if self.report_type:
            if self.holiday_type == "employees":#employee company department category
                # raise UserError((self.report_type))
                # employee_list = self.env['all.employee.list'].sudo().search([]).sorted(key = 'id')
                employee_list = self.employee_id
                emp = employee_list.mapped('id')
                # raise UserError((employee_list))
                    
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': emp,
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}
                # raise UserError((empl, emp))
            if self.holiday_type == "employee":#employee company department category
                # raise UserError((self.report_type))
                # employee_list = self.env['all.employee.list'].sudo().search([]).sorted(key = 'id')
                employee_list = self.employee_ids
                emp = employee_list.mapped('id')
                # raise UserError((employee_list))
                    
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_ids.id,
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}
                # raise UserError((empl, emp))            

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}
            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': self.employee_type,
                        'company_all': False,
                        'is_company': self.is_company}              
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}                
        if self.report_type == 'fnf':
            return self.env.ref('taps_hr.action_fnf_pdf_report').report_action(self, data=data)
        if self.report_type == 'PAYSLIP':
            return self.env.ref('taps_hr.action_pay_slip_pdf_report').report_action(self, data=data)
        if self.report_type == 'SALARYTOP':
            return self.env.ref('taps_hr.action_top_sheet_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'SALARY':
            return self.env.ref('taps_hr.action_salary_sheet_pdf_report').report_action(self, data=data)
        if self.report_type == 'BONUSTOP':
            return self.env.ref('taps_hr.action_bonus_top_sheet_summary_pdf_report').report_action(self, data=data)
        if self.report_type == 'BONUS':
            return self.env.ref('taps_hr.action_bonus_sheet_pdf_report').report_action(self, data=data)
        if self.report_type == 'increment':
            return self.env.ref('taps_hr.action_increment_pdf_report').report_action(self, data=data)
            
        
    def action_generate_xlsx_report(self):
        if self.report_type:
            
            if self.holiday_type == "employee":#employee company department category
                
                empl = self.employee_id
                emp = empl.mapped('id')
                    
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': emp,
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company}
            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': self.employee_type,
                        'company_all': False,
                        'is_company': self.is_company}              
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'employee_type': False,
                        'company_all': self.company_all,
                        'is_company': self.is_company} 
        if self.report_type == 'SALARY':
            return self.salary_xls_template(self, data=data)
        if self.report_type == 'SALARYTOP':
            return self.top_sheet_salary_xls_template(self, data=data)
            # raise UserError(('This Report are not XLSX Format'))
        # else:
            
                   
    
    def salary_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))                

        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        
        catlist = employee.mapped('category_ids.id')
        category = self.env['hr.employee.category'].search([('id', 'in', (catlist))]).sorted(key = 'id', reverse=True)
        
        report_data = []
        emp_data = []
        slnumber=0
        runs = docs.mapped('payslip_run_id')
       
        payslip_runs = self.env['hr.payslip.run'].search([('id', 'in', runs.mapped('id'))])
        
        for payslip in docs:
            slnumber = slnumber+1
            if self.is_company == False:
                emp_data = [
                '',
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.id,
                payslip.employee_id.department_id.parent_id.id,
                payslip.employee_id.grade,
                payslip.employee_id.category_ids.id,
                payslip.employee_id.department_id.name,
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.name,
                payslip.employee_id.department_id.name,
                payslip.employee_id.job_id.name,
                payslip.employee_id.grade,
                format_date(self.env, payslip.employee_id.joining_date),
                payslip._get_work_days_line_total('P'),
                payslip._get_work_days_line_total('X'),
                payslip._get_work_days_line_total('A'),
                payslip._get_work_days_line_total('F'),
                payslip._get_work_days_line_total('H'),
                payslip._get_work_days_line_total('CO'),
                payslip._get_work_days_line_total('AJ'),
                payslip._get_work_days_line_total('OD'),
                payslip._get_work_days_line_total('L'),
                payslip._get_work_days_line_total('CL'),
                payslip._get_work_days_line_total('SL'),
                payslip._get_work_days_line_total('EL'),
                payslip._get_work_days_line_total('ML'),
                payslip._get_work_days_line_total('LW'),
                (payslip._get_work_days_line_total('P') + payslip._get_work_days_line_total('F') +
                 payslip._get_work_days_line_total('H') + payslip._get_work_days_line_total('AJ') + 
                 payslip._get_work_days_line_total('CL') + payslip._get_work_days_line_total('OD') +
                 payslip._get_work_days_line_total('SL') + payslip._get_work_days_line_total('EL')),
                payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL'),
                payslip._get_salary_line_total('BASIC'),
                payslip._get_salary_line_total('HRA'),
                payslip._get_salary_line_total('MEDICAL'), 
                payslip.otHours,
                payslip.otRate,
                payslip._get_salary_line_total('OT'),
                payslip._get_salary_line_total('ARREAR'),
                payslip._get_salary_line_total('ATTBONUS'),
                payslip._get_salary_line_total('CONVENCE'),
                payslip._get_salary_line_total('FOOD'),
                payslip._get_salary_line_total('TIFFIN'),
                payslip._get_salary_line_total('SNACKS'),
                payslip._get_salary_line_total('CAR'),
                payslip._get_salary_line_total('OTHERS_ALW'),
                payslip._get_salary_line_total('INCENTIVE'),
                payslip._get_salary_line_total('RPF'),
                (payslip._get_salary_line_earnings_deduction_total('EARNINGS') +
                 payslip._get_salary_line_total('BASIC') + 
                 payslip._get_salary_line_total('HRA') + 
                 payslip._get_salary_line_total('MEDICAL')),
                payslip._get_salary_line_total('PFR'),
                payslip._get_salary_line_total('PFE'),
                payslip._get_salary_line_total('AIT'),
                payslip._get_salary_line_total('BASIC_ABSENT'),
                payslip._get_salary_line_total('GROSS_ABSENT'),
                payslip._get_salary_line_total('LOAN'),
                payslip._get_salary_line_total('ADV_SALARY'),
                payslip._get_salary_line_total('OTHERS_DED'),
                payslip._get_salary_line_earnings_deduction_total('DED'),
                payslip._get_salary_line_total('NET'),
                payslip.employee_id.bank_account_id.acc_number,
                payslip.employee_id.bank_id.name,
                
                                #round(edata.total),
                
                
            ]
            else:
                
                emp_data = [
                '',
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.id,
                payslip.employee_id.department_id.parent_id.id,
                payslip.employee_id.grade,
                payslip.employee_id.category_ids.id,
                payslip.employee_id.department_id.name,
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.name,
                # payslip.payslip_run_id.name,
                payslip.employee_id.department_id.name,
                payslip.employee_id.job_id.name,
                payslip.employee_id.grade,
                format_date(self.env, payslip.employee_id.joining_date),
                payslip._get_work_days_line_total('P'),
                payslip._get_work_days_line_total('X'),
                payslip._get_work_days_line_total('A'),
                payslip._get_work_days_line_total('F'),
                payslip._get_work_days_line_total('H'),
                payslip._get_work_days_line_total('CO'),
                payslip._get_work_days_line_total('AJ'),
                payslip._get_work_days_line_total('OD'),
                payslip._get_work_days_line_total('L'),
                payslip._get_work_days_line_total('CL'),
                payslip._get_work_days_line_total('SL'),
                payslip._get_work_days_line_total('EL'),
                payslip._get_work_days_line_total('ML'),
                payslip._get_work_days_line_total('LW'),
                (payslip._get_work_days_line_total('P') + payslip._get_work_days_line_total('F') +
                 payslip._get_work_days_line_total('H') + payslip._get_work_days_line_total('AJ') + 
                 payslip._get_work_days_line_total('CL') + payslip._get_work_days_line_total('OD') +
                 payslip._get_work_days_line_total('SL') + payslip._get_work_days_line_total('EL')),
                payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL'),
                payslip._get_salary_line_total('BASIC'),
                payslip._get_salary_line_total('HRA'),
                payslip._get_salary_line_total('MEDICAL'),
                payslip.com_otHours,
                payslip.otRate,
                ((payslip.com_otHours)*(payslip.otRate)),
                0,
                payslip._get_salary_line_total('ATTBONUS'),
                (payslip._get_salary_line_total('CONVENCE') + payslip._get_salary_line_total('CAR')),
                payslip._get_salary_line_total('FOOD'),
                payslip._get_salary_line_total('TIFFIN'),
                payslip._get_salary_line_total('SNACKS'),
                payslip._get_salary_line_total('RPF'),
                ((payslip._get_salary_line_total('BASIC') + 
                  payslip._get_salary_line_total('HRA') +                 
                  payslip._get_salary_line_total('MEDICAL')+
                  ((payslip.com_otHours)*(payslip.otRate))+
                  payslip._get_salary_line_total('ATTBONUS')+
                  payslip._get_salary_line_total('CONVENCE')+ 
                  payslip._get_salary_line_total('FOOD')+
                  payslip._get_salary_line_total('TIFFIN')+
                  payslip._get_salary_line_total('SNACKS')+
                  payslip._get_salary_line_total('CAR')+
                  payslip._get_salary_line_total('RPF'))),
                payslip._get_salary_line_total('PFR'),
                payslip._get_salary_line_total('PFE'),
                payslip._get_salary_line_total('AIT'),
                payslip._get_salary_line_total('BASIC_ABSENT'),
                payslip._get_salary_line_total('GROSS_ABSENT'),
                payslip._get_salary_line_total('LOAN'),
                payslip._get_salary_line_total('ADV_SALARY'),
                payslip._get_salary_line_total('OTHERS_DED'),
                payslip._get_salary_line_earnings_deduction_total('DED'),
                (((payslip._get_salary_line_total('BASIC') + 
                 payslip._get_salary_line_total('HRA') + 
                 payslip._get_salary_line_total('MEDICAL')+
                 ((payslip.com_otHours)*(payslip.otRate))+
                 payslip._get_salary_line_total('ATTBONUS')+
                 payslip._get_salary_line_total('CONVENCE')+ 
                 payslip._get_salary_line_total('FOOD')+
                 payslip._get_salary_line_total('TIFFIN')+
                 payslip._get_salary_line_total('SNACKS')+
                  payslip._get_salary_line_total('CAR')+
                  payslip._get_salary_line_total('RPF')))-payslip._get_salary_line_earnings_deduction_total('DED')),
                payslip.employee_id.bank_account_id.acc_number,
                payslip.employee_id.bank_id.name,
                
                                #round(edata.total),
                
                
            ]
                    
            report_data.append(emp_data)     
                    
        
        categ_data = []
        cdata = []
        for c in category:
            categ_data = []
            
             
            if c.name=='Z-Worker' or c.name=='Z-Staff' or c.name=='Z-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    1,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                
                continue
            if c.name=='B-Worker' or c.name=='B-Staff' or c.name=='B-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    3,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue
            if c.name=='C-Zipper Worker' or c.name=='C-Zipper Staff' or c.name=='C-Button Worker' or c.name=='C-Button Staff' or c.name=='C-Worker' or c.name=='C-Staff':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    4,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue
            if c.name=='Staff' or c.name=='Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    2,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue  
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        
        allemp_data = []
        dept_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                for r in allemp_data:
                    if (r[0] == details.company_id.id) and (r[2] == details.department_id.parent_id.id) and (r[4] == details.department_id.id and r[6]== details.category_ids.id):
                        add = False
                        break
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name, # Section Name
                    details.category_ids.id # Category Id
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        d_data = []
        add = True
        for dep in allemp_data:
            d_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (r[0] == dep[0]) and (r[1] == dep[2]) and (r[3]== dep[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    dep[0],#0 company id
                    dep[2],#1 department id
                    dep[3],#2 department name
                    dep[6] #3 category id
                ]
                dept_data.append(d_data)
            add = True

     
        
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
        
#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                if de.total >2:
#                  de.total=2
#                else:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            # datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B, %Y'),
           data.get('date_to'),
        ]
        common_data.append(common_data)  
        
#             'datas': allemp_data,
# #            'datas': common_data,
# #             'alldays': all_datelist,
#             'dpt': dept_data,
#             'sec': section,
#             'com': company,
#             'cat': cdata,
#             'cd' : common_data,
# #             'stdate': stdate_data,
# #            'lsdate': lsdate_data,
#             'is_com' : data.get('is_company')        
        
        
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#C8EAAB'})
        # worksheet.merge_range('A1:F1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)

        report_small_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 14})
#         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('A2:F2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s SALARY SHEET' % ('','')), report_small_title_style)
#         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        
        column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FFC000', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_title_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#E9ECEF', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#FDE9D9', 'font_size': 11})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})
        row_style = workbook.add_format({'font_size': 11, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        
        format_label_1 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right', 'top': True,  'bottom': True})
        
        format_label_2 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True})
        
        format_label_3 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        
        format_label_4 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right',  'top': True,  'bottom': True, 'bold': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})

        # set the width od the column
     
        
        worksheet.set_column(0, 0, 30)
        worksheet.set_column(2, 2, 30)
        worksheet.set_column(3, 3, 17)
        worksheet.set_column(4, 4, 21)
        worksheet.set_column(5, 5, 30)
        worksheet.set_column(6, 6, 6)
        worksheet.set_column(7, 10, 12)
        worksheet.set_column(11, 13, 9)
        worksheet.set_column(14, 14, 12)
        worksheet.set_column(15, 15, 8)
        worksheet.set_column(16, 16, 10)
        worksheet.set_column(17, 21, 4)
        worksheet.set_column(22, 26, 13)
        worksheet.set_column(27, 28, 10)
        worksheet.set_column(29, 39, 11)
        worksheet.set_column(40, 40, 14)
        worksheet.set_column(41, 47, 14)
        worksheet.set_column(48, 48, 16)
        if self.is_company == False:
            worksheet.set_column(49, 49, 16)
        else:
            worksheet.set_column(49, 49, 25)
        worksheet.set_column(50, 50, 14)
        worksheet.set_column(51, 51, 16)
        worksheet.set_column(52, 52, 25)
        # worksheet.set_column(2, 52, 25)
        
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        #worksheet.merge_range(4, 0, 9, 0, '', merge_format)
        # worksheet.set_column(9, 18, 20)
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        # worksheet.set_column(19, 52, 20)
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        

        worksheet.write(0, 0, 'Reference', column_product_style) 
        worksheet.write(0, 1, 'Emp ID', column_product_style)
        worksheet.write(0, 2, 'Name', column_product_style)
        worksheet.write(0, 3, 'Company', column_product_style)
        worksheet.write(0, 4, 'Section', column_product_style)
        worksheet.write(0, 5, 'Job Position', column_product_style)
        worksheet.write(0, 6, 'Grade', column_product_style)
        worksheet.write(0, 7, 'Joining Date', column_product_style)
        worksheet.write(0, 8, 'Worked Days', column_product_style) 
        worksheet.write(0, 9, 'Gross A. Days', column_product_style) 
        worksheet.write(0, 10, 'Basic A. Day', column_product_style) 
        worksheet.write(0, 11, 'Fridays', column_product_style) 
        worksheet.write(0, 12, 'Holidays', column_product_style) 
        worksheet.write(0, 13, 'Coff Days', column_product_style) 
        worksheet.write(0, 14, 'Adjust Days', column_product_style)
        worksheet.write(0, 15, 'Od Days', column_product_style)
        worksheet.write(0, 16, 'Late Days', column_product_style) 
        worksheet.write(0, 17, 'CL', column_product_style) 
        worksheet.write(0, 18, 'SL', column_product_style) 
        worksheet.write(0, 19, 'EL', column_product_style) 
        worksheet.write(0, 20, 'ML', column_product_style) 
        worksheet.write(0, 21, 'LW', column_product_style) 
        worksheet.write(0, 22, 'Payable Days', column_product_style) 
        worksheet.write(0, 23, 'Gross Salary', column_product_style)  
        worksheet.write(0, 24, 'Basic', column_product_style) 
        worksheet.write(0, 25, 'House Rent', column_product_style) 
        worksheet.write(0, 26, 'Medical', column_product_style) 
        worksheet.write(0, 27, 'OT Hours', column_product_style) 
        worksheet.write(0, 28, 'OT Rate', column_product_style) 
        worksheet.write(0, 29, 'OT', column_product_style)
        worksheet.write(0, 30, 'Arrear', column_product_style)
        worksheet.write(0, 31, 'Att. Bonus', column_product_style)
        worksheet.write(0, 32, 'Convence', column_product_style)
        worksheet.write(0, 33, 'Food', column_product_style)
        worksheet.write(0, 34, 'Tiffin', column_product_style)
        worksheet.write(0, 35, 'Strength', column_product_style)
        

        if self.is_company == False:
            worksheet.write(0, 36, 'Car', column_product_style)
            worksheet.write(0, 37, 'Others Alw', column_product_style)
            worksheet.write(0, 38, 'Incentive', column_product_style)
            worksheet.write(0, 39, 'Rpf', column_product_style)
            worksheet.write(0, 40, 'Total Earnings', column_issued_style)
            worksheet.write(0, 41, 'PF(Empr)', column_product_style)
            worksheet.write(0, 42, 'PF(Empee)', column_product_style)
            worksheet.write(0, 43, 'TDS (AIT)', column_product_style)
            worksheet.write(0, 44, 'Basic A.Deduct', column_product_style)
            worksheet.write(0, 45, 'Gross A.Deduct', column_product_style)
            worksheet.write(0, 46, 'Loan', column_product_style)
            worksheet.write(0, 47, 'Adv. Salary', column_product_style)
            worksheet.write(0, 48, 'Other Deduction', column_product_style)
            worksheet.write(0, 49, 'Total Deduction', column_issued_style)
            worksheet.write(0, 50, 'Net Payable', column_product_style)
            worksheet.write(0, 51, 'Account Number', column_product_style)
            worksheet.write(0, 52, 'Bank Name', column_product_style)
        
        else:
            worksheet.write(0, 36, 'Rpf', column_product_style)
            worksheet.write(0, 37, 'Total Earnings', column_issued_style)
            worksheet.write(0, 38, 'PF(Empr)', column_product_style)
            worksheet.write(0, 39, 'PF(Empee)', column_product_style)
            worksheet.write(0, 40, 'TDS (AIT)', column_product_style)
            worksheet.write(0, 41, 'Basic A.Deduct', column_product_style)
            worksheet.write(0, 42, 'Gross A.Deduct', column_product_style)
            worksheet.write(0, 43, 'Loan', column_product_style)
            worksheet.write(0, 44, 'Adv. Salary', column_product_style)
            worksheet.write(0, 45, 'Other Deduction', column_product_style)
            worksheet.write(0, 46, 'Total Deduction', column_issued_style)
            worksheet.write(0, 47, 'Net Payable', column_product_style)
            worksheet.write(0, 48, 'Account Number', column_product_style)
            worksheet.write(0, 49, 'Bank Name', column_product_style)
        
        
        col = 0
        row = 1
        
        grandtotal = 0
        #company,cdata,dept_data,section,
        # raise UserError((dept_data[0]))
        total_col = 0
        company_count=0
        category_count=0
        departmnt_count=0
        section_count=0
        for line in report_data:
            total_col = len(line)
            break
        sec_sr = 0
        for x in [2,1,3,4]:
            com = company.browse(x)
            if com:
                pr = payslip_runs.filtered(lambda pr: pr.company_id.id == com.id)
                col_com = 1
                group_total = [data for data in report_data if data[3] == com.id]
                for x_c in range(total_col):
                    if x_c == 0:
                        worksheet.write(row, x_c,(str(pr.name)+"(" +str(len(group_total))+")"), format_label_3)
                    elif (x_c > 7):
                        if self.is_company == False:
                            if x_c in (8,9,10,11,12,13,14,58,59):
                                worksheet.write(row, col_com, '', format_label_3)
                            else:
                                column_sum = sum(data[x_c] for data in group_total)
                                worksheet.write(row, col_com, column_sum, format_label_3)
                        else:
                            if x_c in (8,9,10,11,12,13,14,55,56):
                                worksheet.write(row, col_com, '', format_label_3)
                            else:
                                column_sum = sum(data[x_c] for data in group_total)
                                worksheet.write(row, col_com, column_sum, format_label_3)
                            
                        col_com += 1
                row += 1
                
                for cat in cdata:
                    if ((cat[2] == com.id)):
                        col_cat = 1
                        group_total = [y for y in report_data if y[3] == com.id and y[6] == cat[0]]
                        for x_c in range(total_col):
                            if x_c == 0:
                                worksheet.write(row, x_c, (cat[1]+"("+str(len(group_total))+")"), format_label_3)
                            elif (x_c > 7):
                                if self.is_company == False:
                                    if x_c in (8,9,10,11,12,13,14,58,59):
                                        worksheet.write(row, col_cat, '', format_label_3)
                                    else:
                                        column_sum = sum(data[x_c] for data in group_total)
                                        worksheet.write(row, col_cat, column_sum, format_label_3)
                                else:
                                    if x_c in (8,9,10,11,12,13,14,55,56):
                                        worksheet.write(row, col_cat, '', format_label_3)
                                    else:
                                        column_sum = sum(data[x_c] for data in group_total)
                                        worksheet.write(row, col_cat, column_sum, format_label_3)
                                col_cat += 1
                        row += 1
                        for dep in dept_data:
                            if ((cat[2] == dep[0]) and (cat[0] == dep[3])):
                                col_dtp = 1
                                group_total = [y for y in report_data if y[3] == dep[0] and y[6] == dep[3] and y[4] == dep[1]]
                                for x_c in range(total_col):
                                    if x_c == 0:
                                        worksheet.write(row, x_c, (str(dep[2])+"("+str(len(group_total))+")"), format_label_4)
                                    elif (x_c > 7):
                                        if self.is_company == False:
                                            if x_c in (8,9,10,11,12,13,14,58,59):
                                                worksheet.write(row, col_dtp, '', format_label_4)
                                            else:
                                                column_sum = sum(data[x_c] for data in group_total)
                                                worksheet.write(row, col_dtp, column_sum, format_label_4)
                                        else:
                                            if x_c in (8,9,10,11,12,13,14,55,56):
                                                worksheet.write(row, col_dtp, '', format_label_4)
                                            else:
                                                column_sum = sum(data[x_c] for data in group_total)
                                                worksheet.write(row, col_dtp, column_sum, format_label_4)
                                            
                                        col_dtp += 1
                                row += 1
                                sec_sr = 0
                                for line in report_data:
                                    if ((dep[0] == line[3]) and (dep[1] == line[4]) and (dep[3] == line[6])):
                                        if sec_sr == 0:
                                            col_sec = 1
                                            group_total = [y for y in report_data if y[3] == line[3] and y[4] == line[4] and y[6] == line[6]]
                                            for x_c in range(total_col):
                                                if x_c == 0:
                                                    worksheet.write(row, x_c, (str(line[7])+"("+str(len(group_total))+")"), format_label_4)
                                                elif (x_c > 7):
                                                    if self.is_company == False:
                                                        if x_c in (8,9,10,11,12,13,14,58,59):
                                                            worksheet.write(row, col_sec, '', format_label_4)
                                                        else:
                                                            column_sum = sum(data[x_c] for data in group_total)
                                                            worksheet.write(row, col_sec, column_sum, format_label_4)
                                                    else:
                                                        if x_c in (8,9,10,11,12,13,14,55,56):
                                                            worksheet.write(row, col_sec, '', format_label_4)
                                                        else:
                                                            column_sum = sum(data[x_c] for data in group_total)
                                                            worksheet.write(row, col_sec, column_sum, format_label_4)
                                                    col_sec += 1
                                            row += 1                                            
                                        sec_sr += 1
                                        col = 0
                                        col_s = 1
                                        for l in line:
                                            if (col > 7):
                                                worksheet.write(row, col_s, l, row_style)
                                                col_s += 1
                                            col += 1
                                        row += 1
        
        #worksheet.write(com_row, 15, '=SUM(I{0}:I{1})'.format(1, row), column_product_style)
        worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        worksheet.write(row, 5, round(grandtotal,2), report_small_title_style)
        #raise UserError((datefrom,dateto,bankname,categname))
        
        workbook.close()
        output.seek(0)
        # binary_data = output.getvalue()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Salary Sheet')),
            'target': 'self',
        } 

    # raise UserError((top_sheet_salary_xls_template)) 
    def top_sheet_salary_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        if data.get('bank_id'):
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))                

        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
            #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        
        catlist = employee.mapped('category_ids.id')
        category = self.env['hr.employee.category'].search([('id', 'in', (catlist))]).sorted(key = 'id', reverse=True)
        
        report_data = []
        emp_data = []
        slnumber=0
        runs = docs.mapped('payslip_run_id')
       
        payslip_runs = self.env['hr.payslip.run'].search([('id', 'in', runs.mapped('id'))])
        
        for payslip in docs:
            slnumber = slnumber+1
            if self.is_company == False:
                emp_data = [
                '',
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.id,
                payslip.employee_id.department_id.id,
                payslip.employee_id.grade,
                payslip.employee_id.category_ids.id,
                payslip.employee_id.department_id.display_name,
                payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL'),
                payslip._get_salary_line_total('BASIC'),
                payslip._get_salary_line_total('HRA'),
                payslip._get_salary_line_total('MEDICAL'), 
                payslip.otHours,
                payslip.otRate,
                payslip._get_salary_line_total('OT'),
                payslip._get_salary_line_total('ARREAR'),
                payslip._get_salary_line_total('ATTBONUS'),
                payslip._get_salary_line_total('CONVENCE'),
                payslip._get_salary_line_total('FOOD'),
                payslip._get_salary_line_total('TIFFIN'),
                payslip._get_salary_line_total('SNACKS'),
                payslip._get_salary_line_total('CAR'),
                payslip._get_salary_line_total('OTHERS_ALW'),
                payslip._get_salary_line_total('INCENTIVE'),
                payslip._get_salary_line_total('RPF'),
                (payslip._get_salary_line_earnings_deduction_total('EARNINGS') +
                 payslip._get_salary_line_total('BASIC') + 
                 payslip._get_salary_line_total('HRA') + 
                 payslip._get_salary_line_total('MEDICAL')),
                payslip._get_salary_line_total('PFR'),
                payslip._get_salary_line_total('PFE'),
                payslip._get_salary_line_total('AIT'),
                payslip._get_salary_line_total('BASIC_ABSENT'),
                payslip._get_salary_line_total('GROSS_ABSENT'),
                payslip._get_salary_line_total('LOAN'),
                payslip._get_salary_line_total('ADV_SALARY'),
                payslip._get_salary_line_total('OTHERS_DED'),
                payslip._get_salary_line_earnings_deduction_total('DED'),
                payslip._get_salary_line_total('NET'),
                
                                #round(edata.total),
                
                
            ]
            else:
                
                emp_data = [
                '',
                payslip.employee_id.emp_id,
                payslip.employee_id.name,
                payslip.employee_id.company_id.id,
                payslip.employee_id.department_id.id,
                payslip.employee_id.grade,
                payslip.employee_id.category_ids.id,
                payslip.employee_id.department_id.display_name,
                payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL'),
                payslip._get_salary_line_total('BASIC'),
                payslip._get_salary_line_total('HRA'),
                payslip._get_salary_line_total('MEDICAL'),
                payslip.com_otHours,
                payslip.otRate,
                ((payslip.com_otHours)*(payslip.otRate)),
                0,
                payslip._get_salary_line_total('ATTBONUS'),
                (payslip._get_salary_line_total('CONVENCE') + payslip._get_salary_line_total('CAR')),
                payslip._get_salary_line_total('FOOD'),
                payslip._get_salary_line_total('TIFFIN'),
                payslip._get_salary_line_total('SNACKS'),
                payslip._get_salary_line_total('RPF'),
                ((payslip._get_salary_line_total('BASIC') + 
                  payslip._get_salary_line_total('HRA') +                 
                  payslip._get_salary_line_total('MEDICAL')+
                  ((payslip.com_otHours)*(payslip.otRate))+
                  payslip._get_salary_line_total('ATTBONUS')+
                  payslip._get_salary_line_total('CONVENCE')+ 
                  payslip._get_salary_line_total('FOOD')+
                  payslip._get_salary_line_total('TIFFIN')+
                  payslip._get_salary_line_total('SNACKS')+
                  payslip._get_salary_line_total('CAR')+
                  payslip._get_salary_line_total('RPF'))),
                payslip._get_salary_line_total('PFR'),
                payslip._get_salary_line_total('PFE'),
                payslip._get_salary_line_total('AIT'),
                payslip._get_salary_line_total('BASIC_ABSENT'),
                payslip._get_salary_line_total('GROSS_ABSENT'),
                payslip._get_salary_line_total('LOAN'),
                payslip._get_salary_line_total('ADV_SALARY'),
                payslip._get_salary_line_total('OTHERS_DED'),
                payslip._get_salary_line_earnings_deduction_total('DED'),
                (((payslip._get_salary_line_total('BASIC') + 
                 payslip._get_salary_line_total('HRA') + 
                 payslip._get_salary_line_total('MEDICAL')+
                 ((payslip.com_otHours)*(payslip.otRate))+
                 payslip._get_salary_line_total('ATTBONUS')+
                 payslip._get_salary_line_total('CONVENCE')+ 
                 payslip._get_salary_line_total('FOOD')+
                 payslip._get_salary_line_total('TIFFIN')+
                 payslip._get_salary_line_total('SNACKS')+
                  payslip._get_salary_line_total('CAR')+
                  payslip._get_salary_line_total('RPF')))-payslip._get_salary_line_earnings_deduction_total('DED')),
                
                                #round(edata.total),
    				
            ]
                    
            report_data.append(emp_data)     
                    
        
        categ_data = []
        cdata = []
        for c in category:
            categ_data = []
            
             
            if c.name=='Z-Worker' or c.name=='Z-Staff' or c.name=='Z-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    1,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                
                continue
            if c.name=='B-Worker' or c.name=='B-Staff' or c.name=='B-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    3,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue
            if c.name=='C-Zipper Worker' or c.name=='C-Zipper Staff' or c.name=='C-Button Worker' or c.name=='C-Button Staff' or c.name=='C-Worker' or c.name=='C-Staff':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    4,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue
            if c.name=='Staff' or c.name=='Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    2,  #company id
                    len(c.name)
                ]
                cdata.append(categ_data)
                continue  
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        
        allemp_data = []
        dept_data = []
        section_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                for r in allemp_data:
                    if (r[0] == details.company_id.id) and (r[2] == details.department_id.parent_id.id) and (r[4] == details.department_id.id and r[6]== details.category_ids.id):
                        add = False
                        break
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name, # Section Name
                    details.category_ids.id # Category Id
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        d_data = []
        add = True
        for dep in allemp_data:
            d_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (r[0] == dep[0]) and (r[1] == dep[2]) and (r[3]== dep[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    dep[0],#0 company id
                    dep[2],#1 department id
                    dep[3],#2 department name
                    dep[6] #3 category id
                ]
                dept_data.append(d_data)
            add = True
        
        d_data = []
        add = True
        for sec in allemp_data:
            d_data = []
            if section_data:
                i = 0
                for r in section_data:
                    if (r[0] == sec[0]) and (r[1] == sec[2]) and (r[3]== sec[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    sec[0],#0 company id
                    sec[2],#1 department id
                    sec[6], #2 category id
                    sec[4],#3 section id
                    sec[5],#4 section name
                ]
                section_data.append(d_data)
            add = True            
        
        
        emp = employee.sorted(key = 'id')[:1]
    
        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
        
    #     for details in docs:
    #         otTotal = 0
    #         for de in docs:
    #            if de.total >2:
    #              de.total=2
    #            else:
    #             otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            # datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B, %Y'),
           data.get('date_to'),
        ]
        common_data.append(common_data)  
                
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()
    
        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#C8EAAB'})
        # worksheet.merge_range('A1:F1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
    
        report_small_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 14})
    #     worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
        # worksheet.merge_range('A2:F2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
        # worksheet.merge_range('A3:F3', ('TZBD, %s EMPLOYEE %s SALARY SHEET' % ('','')), report_small_title_style)
    #     worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
        # , 'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"??_);_(@_)'
        column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FFC000', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_title_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#E9ECEF', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#FDE9D9', 'font_size': 11,'left': True, 'top': True, 'right': True, 'bottom': True})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})
        row_style = workbook.add_format({'font_size': 11, 'font':'Calibri', 'left': True, 'top': True, 'right': True, 'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        row_style_1 = workbook.add_format({'font_size': 11, 'font':'Calibri', 'valign': 'right', 'top': True, 'bottom': True})
        format_label_1 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right', 'top': True,  'bottom': True})
        
        format_label_2 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True})
        
        format_label_3 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'top', 'bold': True,  'top': True,  'bottom': True,'num_format': '_(* #,##0_);_(* (#,##0);_(* "-"_);_(@_)'})
        
        format_label_4 = workbook.add_format({'bg_color': '#E9ECEF','font':'Calibri', 'font_size': 11, 'valign': 'right',  'top': True,  'bottom': True, 'bold': True})
    
        # set the width od the column
        
        
        worksheet.set_column(0, 0, 52)
        worksheet.set_column(1, 4, 17)
        worksheet.set_column(5, 7, 9)
        worksheet.set_column(8, 14, 12)
        worksheet.set_column(15, 15, 15)
        worksheet.set_column(16, 18, 12)
        worksheet.set_column(19, 23, 14)
        worksheet.set_column(24, 25, 15)
        worksheet.set_column(26, 28, 15)
        
        # worksheet.set_column(2, 52, 25)
        
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        #worksheet.merge_range(4, 0, 9, 0, '', merge_format)
        # worksheet.set_column(9, 18, 20)
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        # worksheet.set_column(19, 52, 20)
        merge_format = workbook.add_format({'align': 'center','valign': 'top'})
        
    
        worksheet.write(0, 0, 'Particulars', column_issued_style)  
        worksheet.write(0, 1, 'Gross', column_issued_style)  
        worksheet.write(0, 2, 'Basic', column_issued_style) 
        worksheet.write(0, 3, 'House Rent', column_issued_style) 
        worksheet.write(0, 4, 'Medical', column_issued_style) 
        worksheet.write(0, 5, 'OT Hours', column_issued_style) 
        worksheet.write(0, 6, 'OT Rate', column_issued_style) 
        worksheet.write(0, 7, 'OT', column_issued_style)
        worksheet.write(0, 8, 'Arrear', column_issued_style)
        worksheet.write(0, 9, 'Att. Bonus', column_issued_style)
        worksheet.write(0, 10, 'Convence', column_issued_style)
        worksheet.write(0, 11, 'Food', column_issued_style)
        worksheet.write(0, 12, 'Tiffin', column_issued_style)
        worksheet.write(0, 13, 'Strength', column_issued_style)
        
    
        if self.is_company == False:
            worksheet.write(0, 14, 'Car', column_issued_style)
            worksheet.write(0, 15, 'Others Alw', column_issued_style)
            worksheet.write(0, 16, 'Incentive', column_issued_style)
            worksheet.write(0, 17, 'Rpf', column_issued_style)
            worksheet.write(0, 18, 'Total Earnings', column_product_style)
            worksheet.write(0, 19, 'PF(Empr)', column_issued_style)
            worksheet.write(0, 20, 'PF(Empee)', column_issued_style)
            worksheet.write(0, 21, 'TDS (AIT)', column_issued_style)
            worksheet.write(0, 22, 'Basic A.Deduct', column_issued_style)
            worksheet.write(0, 23, 'Gross A.Deduct', column_issued_style)
            worksheet.write(0, 24, 'Loan', column_issued_style)
            worksheet.write(0, 25, 'Adv. Salary', column_issued_style)
            worksheet.write(0, 26, 'Other Deduction', column_issued_style)
            worksheet.write(0, 27, 'Total Deduction', column_product_style)
            worksheet.write(0, 28, 'Net Payable', column_product_style)
        
        else:
            worksheet.write(0, 14, 'Rpf', column_issued_style)
            worksheet.write(0, 15, 'Total Earnings', column_product_style)
            worksheet.write(0, 16, 'PF(Empr)', column_issued_style)
            worksheet.write(0, 17, 'PF(Empee)', column_issued_style)
            worksheet.write(0, 18, 'TDS (AIT)', column_issued_style)
            worksheet.write(0, 19, 'Basic A.Deduct', column_issued_style)
            worksheet.write(0, 20, 'Gross A.Deduct', column_issued_style)
            worksheet.write(0, 21, 'Loan', column_issued_style)
            worksheet.write(0, 22, 'Adv. Salary', column_issued_style)
            worksheet.write(0, 23, 'Other Deduction', column_issued_style)
            worksheet.write(0, 24, 'Total Deduction', column_product_style)
            worksheet.write(0, 25, 'Net Payable', column_product_style)
            
                
        col = 0
        row = 1
        
        grandtotal = 0
        #company,cdata,dept_data,section,
        # raise UserError((dept_data[0]))
        total_col = 0
        company_count=0
        category_count=0
        departmnt_count=0
        section_count=0
        for line in report_data:
            total_col = len(line)
            break
        sec_sr = 0
        for x in [2,1,3,4]:
            com = company.browse(x)
            if com:
                pr = payslip_runs.filtered(lambda pr: pr.company_id.id == com.id)
                col_com = 1
                group_total = [data for data in report_data if data[3] == com.id]
                for x_c in range(total_col):
                    if x_c == 0:
                        worksheet.write(row, x_c,(str(pr.name)+"(" +str(len(group_total))+")"), format_label_3)
                    elif (x_c > 7):
                        column_sum = sum(data[x_c] for data in group_total)
                        worksheet.write(row, col_com, column_sum, format_label_3)
                        col_com += 1
                row += 1
                
                for cat in cdata:
                    if ((cat[2] == com.id)):
                        col_cat = 1
                        group_total = [y for y in report_data if y[3] == com.id and y[6] == cat[0]]
                        for x_c in range(total_col):
                            if x_c == 0:
                                worksheet.write(row, x_c, (cat[1]+"("+str(len(group_total))+")"), format_label_3)
                            elif (x_c > 7):
                                column_sum = sum(data[x_c] for data in group_total)
                                worksheet.write(row, col_cat, column_sum, format_label_3)
                                col_cat += 1
                        row += 1
                        for sec in section_data:
                            # raise UserError(('ddd'))
                            if ((cat[2] == sec[0]) and (cat[0] == sec[2])):
                                
                                sec_sr = 0
                                for line in report_data:
                                    if ((sec[0] == line[3]) and (sec[3] == line[4]) and (sec[2] == line[6])):
                                        #raise UserError(('ddd'))
                                        if sec_sr == 0:
                                            col_sec = 1
                                            group_total = [y for y in report_data if y[3] == line[3] and y[4] == line[4] and y[6] == line[6]]
                                            for x_c in range(total_col):
                                                if x_c == 0:
                                                    worksheet.write(row, x_c, (line[7]+"("+str(len(group_total))+")"), row_style_1)
                                                elif (x_c > 7):
                                                    column_sum = sum(data[x_c] for data in group_total)
                                                    worksheet.write(row, col_sec, column_sum, row_style)
                                                    col_sec += 1
                                            row += 1                                            
                                        sec_sr += 1
                                        col = 0
                                        col_s = 1
                                        # for l in line:
                                        #     if (col > 7):
                                        #         worksheet.write(row, col_s, l, row_style)
                                        #         col_s += 1
                                        #     col += 1
                                        # row += 1
        
        #worksheet.write(com_row, 8, '=SUM(B{0}:B{1})'.format(1, row), column_product_style)
        worksheet.write(row, 4, 'Grand Total', report_small_title_style)
        worksheet.write(row, 5, round(grandtotal,2), report_small_title_style)
        #raise UserError((datefrom,dateto,bankname,categname))
        
        workbook.close()
        output.seek(0)
        # binary_data = output.getvalue()
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('Top Sheet Salary')),
            'target': 'self',
        } 


class PaySlipReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.pay_slip_pdf_template'
    _description = 'Pay Slip Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        # raise UserError((data.get('employee_id')))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('employee_id.department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.id', 'in', (data.get('employee_id'))))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))    
        
        
        # raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        emplist = docs.mapped('employee_id.id')
        # friday_p = self.env['hr.attendance'].search([('employee_id', 'in', (emplist)),('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to')),('inFlag', 'in', ('FP','HP'))])

        friday_p = self.env['hr.attendance'].read_group(
                    [('employee_id', 'in', (emplist)),('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to')),('inFlag', 'in', ('FP','HP'))],
                    ['employee_id'],
                    ['employee_id', 'id:count'],
                    lazy=False
                )
        
        # raise UserError((emplist))
        common_data = []
        for res in friday_p:
            employee_id = res['employee_id'][0] if res.get('employee_id') else None
            employee_count = res['employee_id']
            
            common_data.append({
                'employee_id': employee_id,
                'count': employee_count
            })
            
        
        # fp_days = len(friday_precord)
        # fp_hours = sum(friday_precord.mapped('worked_hours'))         
        # raise UserError((friday_p.employee_id.name))
        # holiday_p = self.env['hr.attendance'].search([('employee_id', 'in', (docs.mapped('employee_id.id'))),('attDate', '>=',data.get('date_from')),('attDate', '<=',data.get('date_to')),('inFlag', '=', 'HP')])
        # hp_days = len(holiday_precord)
        # hp_hours = sum(holiday_precord.mapped('worked_hours'))                
        # fp = 0
        # hp = 0
        # fphp = 0
        # common_data = []
        # for details in friday_p:
        #     fphp = 0
        # for de in docs:
        #     if details.employee_id.id == de.employee_id.id:
        #         fphp = fphp + len(details)
                    # if details.employee_id.id == de.employee_id.id and details.inFlag == 'FP':
                    #     fphp = fp + len(details)
                    # if details.employee_id.id == de.employee_id.id and details.inFlag == 'HP':
                    #     hp = hp + len(details)
                        
                # raise UserError((fphp,details.employee_id.name))
            
            # common_data = [
            #     data.get('report_type'),
            #     data.get('bank_id'),
            #     data.get('date_from'),
            #     data.get('date_to'),
            #     details.employee_id.id,
            #     fphp,
            # ]
            # common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }    

class SalaryTopSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.top_sheet_pdf_template'
    _description = 'Salary Top Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("top_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
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
            domain.append(('employee_id.id', 'in', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))    
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((common_data[2]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        }
    
class SalarySheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.salary_sheet_pdf_template'
    _description = 'Salary Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("salary_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
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
            domain.append(('employee_id.id', 'in', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))    
        
        
        #raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        #raise UserError((emplist)) ,department_id.parent_id.id,department_id.id
        
        
        catlist = employee.mapped('category_ids.id')
        category = self.env['hr.employee.category'].search([('id', 'in', (catlist))]).sorted(key = 'id', reverse=True)
        
        categ_data = []
        cdata = []
        for c in category:
            categ_data = []
            if c.name=='Z-Worker' or c.name=='Z-Staff' or c.name=='Z-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    1  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='B-Worker' or c.name=='B-Staff' or c.name=='B-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    3  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='C-Zipper Worker' or c.name=='C-Zipper Staff' or c.name=='C-Button Worker' or c.name=='C-Button Staff' or c.name=='C-Worker' or c.name=='C-Staff':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    4  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='Staff' or c.name=='Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    2  #company id
                ]
                cdata.append(categ_data)
                continue  
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        allemp_data = []
        dept_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                for r in allemp_data:
                    if (r[0] == details.company_id.id) and (r[2] == details.department_id.parent_id.id) and (r[4] == details.department_id.id and r[6]== details.category_ids.id):
                        add = False
                        break
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name, # Section Name
                    details.category_ids.id # Category Id
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        d_data = []
        add = True
        for dep in allemp_data:
            d_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (r[0] == dep[0]) and (r[1] == dep[2]) and (r[3]== dep[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    dep[0],#0 company id
                    dep[2],#1 department id
                    dep[3],#2 department name
                    dep[6] #3 category id
                ]
                dept_data.append(d_data)
            add = True
            
       
        
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
        
#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                if de.total >2:
#                  de.total=2
#                else:
#                 otTotal = otTotal + de.total
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B, %Y'),
#            data.get('date_to'),
        ]
        common_data.append(common_data)
        #raise UserError((allemp_data))

        
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': allemp_data,
#            'datas': common_data,
#             'alldays': all_datelist,
            'dpt': dept_data,
            'sec': section,
            'com': company,
            'cat': cdata,
            'cd' : common_data,
#             'stdate': stdate_data,
#            'lsdate': lsdate_data,
            'is_com' : data.get('is_company')
        }
    
class BonusTopSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.bonus_top_sheet_pdf_template'
    _description = 'Bonus Top Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("bonus_top_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
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
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))    
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        #raise UserError((emplist)) ,department_id.parent_id.id,department_id.id
        service_length = []
        s_length = []
        
        for record in employee:
            if record:
                s_length = []
                currentDate = fields.datetime.strptime(str(data.get('date_to')),'%Y-%m-%d')
                deadlineDate = fields.datetime.strptime(str(record.joining_date),'%Y-%m-%d')
                
                daysLeft = deadlineDate - currentDate
                years = ((daysLeft.total_seconds())/(365.242*24*3600))
                years = abs(years)
                yearsInt=int(years)
                months=(years-yearsInt)*12
                months = abs(months)
                monthsInt=int(months)
                days=(months-monthsInt)*(365.242/12)
                days = abs(days)
                daysInt=int(days)
                
                length = str(int(yearsInt)) + ' Years ' + str(int(monthsInt)) + ' Months ' + str(int(daysInt)) + ' Days '
                s_length =[
                    record.id,
                    length
                ]
                service_length.append(s_length)
        
        catlist = employee.mapped('category_ids.id')
        category = self.env['hr.employee.category'].search([('id', 'in', (catlist))]).sorted(key = 'id', reverse=True)
        
        categ_data = []
        cdata = []
        for c in category:
            categ_data = []
            if c.name=='Z-Worker' or c.name=='Z-Staff' or c.name=='Z-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    1  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='B-Worker' or c.name=='B-Staff' or c.name=='B-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    3  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='C-Zipper Worker' or c.name=='C-Zipper Staff' or c.name=='C-Button Worker' or c.name=='C-Button Staff' or c.name=='C-Worker' or c.name=='C-Staff':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    4  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='Staff' or c.name=='Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    2  #company id
                ]
                cdata.append(categ_data)
                continue  
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        allemp_data = []
        dept_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                for r in allemp_data:
                    if (r[0] == details.company_id.id) and (r[2] == details.department_id.parent_id.id) and (r[4] == details.department_id.id and r[6]== details.category_ids.id):
                        add = False
                        break
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name, # Section Name
                    details.category_ids.id # Category Id
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        d_data = []
        add = True
        for dep in allemp_data:
            d_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (r[0] == dep[0]) and (r[1] == dep[2]) and (r[3]== dep[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    dep[0],#0 company id
                    dep[2],#1 department id
                    dep[3],#2 department name
                    dep[6] #3 category id
                ]
                dept_data.append(d_data)
            add = True
            
       
        
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
        
        p_date= datetime.strptime(data.get('date_to'), '%Y-%m-%d')
        p_date+=timedelta(days=1)
        
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B, %Y'),
            p_date.strftime('%d-%m-%Y'),
        ]
        common_data.append(common_data)
        
       
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': allemp_data,
#            'datas': common_data,
#             'alldays': all_datelist,
            'dpt': dept_data,
            'sec': section,
            'com': company,
            'cat': cdata,
            'cd' : common_data,
           
            'length': service_length,
#            'lsdate': lsdate_data,
            'is_com' : data.get('is_company')
        }
    
class BonusSheetReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.bonus_sheet_pdf_template'
    _description = 'Bonus Sheet Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("bonus_sheet_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '=', data.get('date_to')))
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
            domain.append(('employee_id.id', 'in', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))    
        
        
#         raise UserError((domain))
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        #raise UserError((emplist)) ,department_id.parent_id.id,department_id.id
        service_length = []
        s_length = []
        
        for record in employee:
            if record:
                s_length = []
                currentDate = fields.datetime.strptime(str(data.get('date_to')),'%Y-%m-%d')
                deadlineDate = fields.datetime.strptime(str(record.joining_date),'%Y-%m-%d')
                
                daysLeft = deadlineDate - currentDate
                years = ((daysLeft.total_seconds())/(365.242*24*3600))
                years = abs(years)
                yearsInt=int(years)
                months=(years-yearsInt)*12
                months = abs(months)
                monthsInt=int(months)
                days=(months-monthsInt)*(365.242/12)
                days = abs(days)
                daysInt=int(days)
                
                length = str(int(yearsInt)) + ' Years ' + str(int(monthsInt)) + ' Months ' + str(int(daysInt)) + ' Days '
                s_length =[
                    record.id,
                    length
                ]
                service_length.append(s_length)
        
        catlist = employee.mapped('category_ids.id')
        category = self.env['hr.employee.category'].search([('id', 'in', (catlist))]).sorted(key = 'id', reverse=True)
        
        categ_data = []
        cdata = []
        for c in category:
            categ_data = []
            if c.name=='Z-Worker' or c.name=='Z-Staff' or c.name=='Z-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    1  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='B-Worker' or c.name=='B-Staff' or c.name=='B-Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    3  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='C-Zipper Worker' or c.name=='C-Zipper Staff' or c.name=='C-Button Worker' or c.name=='C-Button Staff' or c.name=='C-Worker' or c.name=='C-Staff':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    4  #company id
                ]
                cdata.append(categ_data)
                continue
            if c.name=='Staff' or c.name=='Expatriate':
                categ_data = [
                    c.id, #category id
                    c.name, #category name
                    2  #company id
                ]
                cdata.append(categ_data)
                continue  
        
        sectionlist = employee.mapped('department_id.id')
        section = self.env['hr.department'].search([('id', 'in', (sectionlist))])
        
        
        parentdpt = section.mapped('parent_id.id')
        department = self.env['hr.department'].search([('id', 'in', (parentdpt))])
        
        
        com = employee.mapped('company_id.id')
        company = self.env['res.company'].search([('id', 'in', (com))])
        
        allemp_data = []
        dept_data = []
        emp_data = []
        add = True
        for details in employee:
            emp_data = []
            #raise UserError(('allemp_data'))
            if allemp_data:
                for r in allemp_data:
                    if (r[0] == details.company_id.id) and (r[2] == details.department_id.parent_id.id) and (r[4] == details.department_id.id and r[6]== details.category_ids.id):
                        add = False
                        break
            if add == True:
                emp_data = [
                    details.company_id.id,
                    details.company_id.name,
                    details.department_id.parent_id.id, # Department ID
                    details.department_id.parent_id.name, # Department Name
                    details.department_id.id, # Section ID
                    details.department_id.name, # Section Name
                    details.category_ids.id # Category Id
                ]
                allemp_data.append(emp_data)
            add = True
        #raise UserError((allemp_data))
        d_data = []
        add = True
        for dep in allemp_data:
            d_data = []
            if dept_data:
                i = 0
                for r in dept_data:
                    if (r[0] == dep[0]) and (r[1] == dep[2]) and (r[3]== dep[6]):
                        i = i+1
                        add = False
                        break
            if add == True:
                d_data = [
                    dep[0],#0 company id
                    dep[2],#1 department id
                    dep[3],#2 department name
                    dep[6] #3 category id
                ]
                dept_data.append(d_data)
            add = True
            
       
        
        emp = employee.sorted(key = 'id')[:1]

        if data.get('mode_company_id'):
            heading_type = emp.company_id.name
        if data.get('department_id'):
            heading_type = emp.department_id.name
        if data.get('category_id'):
            heading_type = emp.category_ids.name
        if data.get('employee_id'):
            heading_type = emp.name 
        
        p_date= datetime.strptime(data.get('date_to'), '%Y-%m-%d')
        p_date+=timedelta(days=1)
        
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            datetime.strptime(data.get('date_to'), '%Y-%m-%d').strftime('%B, %Y'),
            p_date.strftime('%d-%m-%Y'),
        ]
        common_data.append(common_data)
        
       
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': allemp_data,
#            'datas': common_data,
#             'alldays': all_datelist,
            'dpt': dept_data,
            'sec': section,
            'com': company,
            'cat': cdata,
            'cd' : common_data,
           
            'length': service_length,
#            'lsdate': lsdate_data,
            'is_com' : data.get('is_company')
        }
    

    
class FullAndFinalSettlementReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.fnf_pdf_template'
    _description = 'Full & Final Settlement Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        # raise UserError((data.get('employee_id')))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('date_from', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', 'in', data.get('employee_id')))
        if data.get('employee_ids'):
            domain.append(('employee_id.id', '=', data.get('employee_ids')))            
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))   
                struct_id.name
       
        domain.append(('struct_id.name', '=','F&F'))  
        # domain.append(('employee_id.active', 'in',(False,True)))
        raise UserError((domain))
        att_obj = self.env['hr.attendance']
        docs = self.env['hr.payslip'].search(domain).sorted(key = 'employee_id', reverse=False)
        
        # if len(docs) <=0:
        #     raise Warning(_("Full & Final Settlement not Found"))
            
        # raise UserError((docs.id))

#         for details in docs:
#             otTotal = 0
#             for de in docs:
#                 otTotal = otTotal + de.total
        friday_precord = att_obj.search([('employee_id', 'in', (data.get('employee_id'))),('attDate', '>=', data.get('date_from')),('attDate', '<=', data.get('date_to')),('inFlag', '=', 'FP')])
        fp_days = len(friday_precord)
        fp_hours = sum(friday_precord.mapped('worked_hours')) 
        
        holiday_precord = att_obj.search([('employee_id', '=', (data.get('employee_id'))),('attDate', '>=',data.get('date_from')),('attDate', '<=',data.get('date_to')),('inFlag', '=', 'HP')])
        hp_days = len(holiday_precord)
        hp_hours = sum(holiday_precord.mapped('worked_hours'))        
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            data.get('date_to'),
            fp_days,
            fp_hours,
            hp_days,
            hp_hours,
        ]
        common_data.append(common_data)
        # raise UserError((common_data[0],common_data[1],common_data[2],common_data[3]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.payslip',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist,
            'is_com' : data.get('is_company')
        } 
    
    
class WorkerIncrementLetter(models.AbstractModel):
    _name = 'report.taps_hr.increment_pdf_template'
    _description = 'Worker Increment Letter Template'       
    
    def _get_report_values(self, docids, data=None):
        domain = []
        #raise UserError(("pay_slip_pdf_template"))
        #if data.get('bank_id')==False:
            #domain.append(('code', '=', data.get('report_type')))
        if data.get('date_from'):
            domain.append(('increment_id.increment_month', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('increment_id.increment_month', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            #str = re.sub("[^0-9]","",data.get('mode_company_id'))
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            #str = re.sub("[^0-9]","",data.get('department_id'))
            domain.append(('employee_id.department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            #str = re.sub("[^0-9]","",data.get('category_id'))
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.id', 'in', data.get('employee_id')))
        if data.get('bank_id'):
            #str = re.sub("[^0-9]","",data.get('employee_id'))
            domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
        if data.get('company_all'):
            if data.get('company_all')=='allcompany':
                domain.append(('employee_id.company_id.id', 'in',(1,2,3,4)))   
                # struct_id.name
        # domain.append(('struct_id.name', '=','F&F'))  
        
        # att_obj = self.env['hr.attendance']
        docs = self.env['increment.promotion.line'].search(domain).sorted(key = 'employee_id', reverse=False)
        
        
        p_date= datetime.strptime(data.get('date_from'), '%Y-%m-%d')
        p_date+=timedelta(days=1)
            
        common_data = [
            data.get('report_type'),
            data.get('bank_id'),
            data.get('date_from'),
            p_date.strftime('%d-%B-%Y'),
            
        ]
        common_data.append(common_data)
        # raise UserError((common_data[0],common_data[1],common_data[2],common_data[3]))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'increment.promotion.line',
            'docs': docs,
            'datas': common_data,
            
            'is_com' : data.get('is_company')
        }