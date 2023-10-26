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

class HeadwisePDFReport(models.TransientModel):
    _name = 'kpi.objective.pdf.report'
    _description = 'KPI Objective Report'    

    is_company = fields.Boolean(readonly=False, default=False)
    date_from = fields.Date('Date from', required=True, readonly=False, default=lambda self: self._compute_from_date())
    date_to = fields.Date('Date to', required=True, readonly=False, default=lambda self: self._compute_to_date())
    report_type = fields.Selection([
        ('score',	'Scorecard'),
        ('scorequarter',	'Scorecard Quarterly'),
        ('kpi',	'KPI Objective'),
        ('plan',	'KPI objective with Action Plan'),],
        string='Report Type', required=True,
        help='Report Type', default='score')
    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(), required=True)    
    holiday_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('companyall', 'By All Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
    employee_id = fields.Many2one(
        'hr.employee',  domain="['|', ('active', '=', False), ('active', '=', True)]", string='Employee', index=True, readonly=False, ondelete="restrict", default=lambda self: self.env.context.get('default_employee_id') or self.env.user.employee_id)    
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  domain="[('parent_id', '=', False)]", string='Department', readonly=False)

    
    employee_type = fields.Selection([
        ('staff', 'Staffs'),
        ('worker', 'Workers'),
        ('expatriate', 'Expatriates'),
        ('cstaff', 'C-Staffs'),
        ('cworker', 'C-Workers')],
        string='Employee Type', required=False)
    
    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED')],
        string='All Company', required=False)   
    
    file_data = fields.Binary(readonly=True, attachment=False) 

    
    @staticmethod
    def _get_year_list():
        current_year = datetime.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 1):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((next_year, year_label))
        return year_options     

    @staticmethod
    def _get_default_year():
        current_year = datetime.today().year
        return str(current_year+1)  

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
            #else:
            #    holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
    # generate PDF report
    def action_print_report(self):
        if self.report_type:
            if self.holiday_type == "employee":#employee  company department category
                #raise UserError((self.report_type))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id,
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}

            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'report_type': self.report_type,
                        'bank_id': False,
                        'company_all': False,
                        'employee_type': False,
                        'year': self.year}
                
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
                        'year': self.year}              
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
                        'year': self.year}
                
#         return self.env.ref('taps_hr.action_kpi_objective_pdf_report').report_action(self, data=data)
        if self.report_type == 'score':
            return self.env.ref('taps_hr.action_kpi_objective_score_pdf_report').report_action(self, data=data)
        if self.report_type == 'scorequarter':
            return self.env.ref('taps_hr.action_kpi_objective_score_quarter_pdf_report').report_action(self, data=data)
        if self.report_type == 'kpi':
            return self.env.ref('taps_hr.action_kpi_objective_pdf_report').report_action(self, data=data)
        else:
            raise UserError(('This Report are not PDF Format'))

    
    
    def action_generate_xlsx_report(self):
        if self.report_type:
        # if self.report_type == 'plan':
        #     start_time = fields.datetime.now()
            if self.holiday_type == "employee":#employee  company department category
                #raise UserError(('sfefefegegegeeg'))
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': self.employee_id.id, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "company":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': self.mode_company_id.id, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'report_type': False,
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "department":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': self.department_id.id, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "category":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': self.category_id.id, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "emptype":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'employee_type': self.employee_type,
                        'company_all': False,
                        'year': self.year}
                
            if self.holiday_type == "companyall":
                data = {'date_from': self.date_from, 
                        'date_to': self.date_to, 
                        'mode_company_id': False, 
                        'department_id': False, 
                        'category_id': False, 
                        'employee_id': False, 
                        'bank_id': False,
                        'company_all': self.company_all,
                        'year': self.year}
        if self.report_type == 'score':
            return self.score_xls_template(self, data=data)
        if self.report_type == 'scorequarter':
            return self.scorequarter_xls_template(self, data=data)
        if self.report_type == 'kpi':
            return self.kpi_xls_template(self, data=data)
        if self.report_type == 'plan':
            return self.plan_xls_template(self, data=data)         
        else:
            raise UserError(('This Report are not XLSX Format'))


    def score_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
#         if data.get('date_from'):
#             domain.append(('date_from', '=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '=', data.get('date_to')))
        if data.get('year'):
            # raise UserError((data.get('year')))
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))   
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.parent_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append(('code', '=', 'NET'))
        
        
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        docs = None
        datefrom = data.get('date_from')
        dateto = data.get('date_to')

        emply = docs1.mapped('employee_id')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})        
        for emp in emply:
            if emp.company_id.id == 1:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Zipper','$ PAT (Thousand) - Zipper')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            elif emp.company_id.id == 3:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Metal Trims','$ PAT (Thousand) - Metal Trims')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            else:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Zipper','$ PAT (Thousand) - Zipper','$ Revenue (Thousand)  - Metal Trims','$ PAT (Thousand) - Metal Trims')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            
            docs = docs2 | docs1.filtered(lambda x: x.employee_id.id == emp.id)

            # raise UserError((docs2))
            
            report_data = []
            emp_data = []
            slnumber=0
            for edata in docs:
                slnumber = slnumber+1
                emp_data = [
                    slnumber,
                    edata.name,
                    edata.description,
                    round(edata.baseline,2),
                    round(edata.target,2),
                    (edata.weight/100),
                    'Target',
                    edata.t_apr,
                    edata.t_may,
                    edata.t_jun,
                    edata.t_jul,
                    edata.t_aug,
                    edata.t_sep,
                    edata.t_oct,
                    edata.t_nov,
                    edata.t_dec,
                    edata.t_jan,
                    edata.t_feb,
                    edata.t_mar,
                    edata.y_t_ytd,
                    'ACVD',
                    edata.a_apr,
                    edata.a_may,
                    edata.a_jun,
                    edata.a_jul,
                    edata.a_aug,
                    edata.a_sep,
                    edata.a_oct,
                    edata.a_nov,
                    edata.a_dec,
                    edata.a_jan,
                    edata.a_feb,
                    edata.a_mar,
                    edata.y_a_ytd,
                    'Weightage',
                    edata.apr,
                    edata.may,
                    edata.jun,
                    edata.jul,
                    edata.aug,
                    edata.sep,
                    edata.oct,
                    edata.nov,
                    edata.dec,
                    edata.jan,
                    edata.feb,
                    edata.mar,
                    edata.y_ytd,
                    edata.employee_id.id,
                ]
                report_data.append(emp_data)
            month = docs.mapped('month')[1:]
            mm = 'Month'
            for m in month:
                if m == 'apr':
                    mm = 'April'
                elif m == 'may':
                    mm = 'May'
                elif m == 'jun':
                    mm = 'Jun'
                elif m == 'jul':
                    mm = 'July'
                elif m == 'aug':
                    mm = 'August'
                elif m == 'sep':
                    mm = 'September'
                elif m == 'oct':
                    mm = 'October'
                elif m == 'nov':
                    mm = 'November'
                elif m == 'dec':
                    mm = 'December'
                elif m == 'jan':
                    mm = 'January'
                elif m == 'feb':
                    mm = 'February'
                elif m == 'mar':
                    mm = 'March'
            weight = 0
            apr = 0
            may = 0
            jun = 0
            jul = 0
            aug = 0
            sep = 0
            oct = 0
            nov = 0
            dec = 0
            jan = 0
            feb = 0
            mar = 0
            ytd = 0
            for de in docs1.filtered(lambda x: x.employee_id.id == emp.id):
                weight = weight + de.weight
                apr = apr + de.apr
                may = may + de.may
                jun = jun + de.jun
                jul = jul + de.jul
                aug = aug + de.aug
                sep = sep + de.sep
                oct = oct + de.oct
                nov = nov + de.nov
                dec = dec + de.dec
                jan = jan + de.jan
                feb = feb + de.feb
                mar = mar + de.mar
                ytd = ytd + de.y_ytd
                
                
            worksheet = workbook.add_worksheet(('%s - %s' % (emp.pin,emp.name)))
            worksheet.set_zoom(74)
            report_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 16, 'bg_color': '#343A40','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_title_style1 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'font_size': 13, 'bg_color': '#343A40','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_column_style = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12})
            report_column_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12,'bold': True,'font_color':'#FFFFFF','bg_color': '#714B35', 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00%'})
            report_column_style_2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00'})
           
            report_column_style_2.set_text_wrap()
            report_column_style_3 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00%'})
            worksheet.merge_range('A1:E1',('%s' % (emp.name)), report_title_style)
            
            # img = io.BytesIO(base64.b64decode(emp.image_1920))
            # worksheet.insert_image(0, 1, '', {'image_data': img, "x_scale": 0.06, "y_scale": 0.06,'align': 'center','valign': 'vcenter' })
            
            # img_ = io.BytesIO(base64.b64decode(emp.parent_id.image_1920))
            # worksheet.insert_image(0, 23, '', {'image_data': img_, "x_scale": 0.3, "y_scale": 0.3, 'object_position': 1})
            
            worksheet.merge_range('F1:M1', 'KPI Scorecard [Challenged By]', report_title_style)
            worksheet.merge_range('N1:X1', ('%s' % (emp.parent_id.name)), report_title_style)
    
            report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14, 'border': True,'num_format': '0.00%'})
    #         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
            worksheet.merge_range('A2:E2',('%s' % (emp.job_title)), report_title_style1)
            worksheet.merge_range('F2:M2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_title_style1)
            worksheet.merge_range('N2:X2', ('%s' % (emp.parent_id.job_title)), report_title_style1)
            # worksheet.merge_range('C3:F3', ('KPI objective'), report_small_title_style)
            # worksheet.merge_range('A4:F4', ('%s - %s' % (emp.pin,emp.name)), report_title_style)
            worksheet.merge_range('F4:F4', "",report_title_style)
            # worksheet.merge_range('I4:L4', ('Weekly Plan'), report_title_style)
    #         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
            merge_format = workbook.add_format({'align': 'center','valign': 'vcenter', 'left': True, 'top': True, 'right': True, 'bottom': True})
            merge_format.set_text_wrap()
            merge_format_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 16, 'font_color':'#FFFFFF'})
            merge_format_.set_text_wrap()
            
            column_product_style = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            column_product_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B35', 'font_size': 14, 'font_color':'#FFFFFF', 'border': True})
            column_product_style2 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True})
            column_product_style_3 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00%'})
            column_product_style_5 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            column_product_style_6 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            
            column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12, 'border': True})
            column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12, 'border': True})
            row_categ_style = workbook.add_format({'border': True})
            gray_style = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            gray_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            gray_style_1 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True,"num_format": "0.00%"})
    
            # set the width od the column
            # _range = len(report_data)
            percent_format = workbook.add_format({"num_format": "0%"})
            worksheet.freeze_panes(6, 0)


            worksheet.write(2, 2, 'WEIGHT', column_product_style_6)
            worksheet.write(2, 3, 'APR', column_product_style_6)
            worksheet.write(2, 4, 'MAY', column_product_style_6)
            worksheet.write(2, 5, 'JUN', column_product_style_6)
            worksheet.write(2, 6, 'JUL', column_product_style_6)
            worksheet.write(2, 7, 'AUG', column_product_style_6)
            worksheet.write(2, 8, 'SEP', column_product_style_6)
            worksheet.write(2, 9, 'OCT', column_product_style_6)
            worksheet.write(2, 10, 'NOV', column_product_style_6)
            worksheet.write(2, 11, 'DEC', column_product_style_6)
            worksheet.write(2, 12, 'JAN', column_product_style_6)
            worksheet.write(2, 13, 'FEB', column_product_style_6)
            worksheet.write(2, 14, 'MAR', column_product_style_6)
            worksheet.write(2, 15, 'YTD', column_product_style_5)

             
            
            worksheet.write(3, 2, weight, column_product_style_6)
            worksheet.write(3, 3, apr, column_product_style_6)
            worksheet.write(3, 4, may, column_product_style_6)
            worksheet.write(3, 5, jun, column_product_style_6)
            worksheet.write(3, 6, jul, column_product_style_6)
            worksheet.write(3, 7, aug, column_product_style_6)
            worksheet.write(3, 8, sep, column_product_style_6)
            worksheet.write(3, 9,  oct, column_product_style_6)
            worksheet.write(3, 10, nov, column_product_style_6)
            worksheet.write(3, 11, dec, column_product_style_6)
            worksheet.write(3, 12, jan, column_product_style_6)
            worksheet.write(3, 13, feb, column_product_style_6)
            worksheet.write(3, 14, mar, column_product_style_6)
            worksheet.write(3, 15, ytd, column_product_style_5)
            # raise UserError((weight + de.weight))
            
            worksheet.set_column(0,0,3)
            worksheet.set_column(1,1,50)
            worksheet.set_column(2,2,20)
            worksheet.set_column(3,4,8)
            worksheet.set_column(5,6,10.20)
            
            worksheet.set_row(0, 20)
            
            worksheet.write(5, 0, 'SL.', column_product_style)
            worksheet.write(5, 1, 'Objectives', column_product_style)
            worksheet.write(5, 2, 'Description', column_product_style)
            worksheet.write(5, 3, 'Baseline', column_product_style)
            worksheet.write(5, 4, 'Target', column_product_style)
            worksheet.write(5, 5, 'Weight', column_product_style)
            worksheet.write(5, 6, 'Particulars', column_product_style)
            worksheet.write(5, 7, 'Apr', column_product_style)
            worksheet.write(5, 8, 'May', column_product_style)
            worksheet.write(5, 9, 'Jun', column_product_style)
            worksheet.write(5, 10, 'Jul', column_product_style)
            worksheet.write(5, 11, 'Aug', column_product_style)
            worksheet.write(5, 12, 'Sep', column_product_style)
            worksheet.write(5, 13, 'Oct', column_product_style)
            worksheet.write(5, 14, 'Nov', column_product_style)
            worksheet.write(5, 15, 'Dec', column_product_style)
            worksheet.write(5, 16, 'Jan', column_product_style)
            worksheet.write(5, 17, 'Feb', column_product_style)
            worksheet.write(5, 18, 'Mar', column_product_style)
            worksheet.write(5, 19, 'YTD', column_product_style)
            col = 0
            row=6
            grandtotal = 0
            slnumber = 0
            total_weight_35 = 0
            total_weight_36 = 0
            total_weight_37 = 0
            total_weight_38 = 0
            total_weight_39 = 0
            total_weight_40 = 0
            total_weight_41 = 0
            total_weight_42 = 0
            total_weight_43 = 0
            total_weight_44 = 0
            total_weight_45 = 0
            total_weight_46 = 0
            total_weight_47 = 0
            # worksheet.set_row(8, 35)
            worksheet.merge_range(row, 0, row, 19, 'Revenue & PAT', merge_format_)
            row=7
            
            # filtered_data = [line for line in report_data if line[48] == emp.id]
            # raise UserError((filtered_data))
            for line in report_data:
                mrg_val = None    
                if not line[48]:
                    total_weight_35 += line[35]
                    total_weight_36 += line[36]
                    total_weight_37 += line[37]
                    total_weight_38 += line[38]
                    total_weight_39 += line[39]
                    total_weight_40 += line[40]
                    total_weight_41 += line[41]
                    total_weight_42 += line[42]
                    total_weight_43 += line[43]
                    total_weight_44 += line[44]
                    total_weight_45 += line[45]
                    total_weight_46 += line[46]
                    total_weight_47 += line[47]
                    slnumber += 1
                    col=0
                    line.pop(48)
                    if line[1]:
                        worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                        worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                        worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                        worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                        worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                        worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                        # worksheet.write(sum(row, 0, row[2], 0, l, merge_format))
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, '', report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                                # total_sum += l
                        elif col == 19 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 19 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1

                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_35/100, report_column_style_)
            worksheet.write(row, 8, total_weight_36/100, report_column_style_)
            worksheet.write(row, 9, total_weight_37/100, report_column_style_)
            worksheet.write(row, 10, total_weight_38/100, report_column_style_)
            worksheet.write(row, 11, total_weight_39/100, report_column_style_)
            worksheet.write(row, 12, total_weight_40/100, report_column_style_)
            worksheet.write(row, 13, total_weight_41/100, report_column_style_)
            worksheet.write(row, 14, total_weight_42/100, report_column_style_)
            worksheet.write(row, 15, total_weight_43/100, report_column_style_)
            worksheet.write(row, 16, total_weight_44/100, report_column_style_)
            worksheet.write(row, 17, total_weight_45/100, report_column_style_)
            worksheet.write(row, 18, total_weight_46/100, report_column_style_)
            worksheet.write(row, 19, total_weight_47/100, report_column_style_)
            row+=1
            
                    
            worksheet.merge_range(row, 0, row, 19, 'Objective / Score', merge_format_)
            row+=1

            total_weight_35_ = 0
            total_weight_36_ = 0
            total_weight_37_ = 0
            total_weight_38_ = 0
            total_weight_39_ = 0
            total_weight_40_ = 0
            total_weight_41_ = 0
            total_weight_42_ = 0
            total_weight_43_ = 0
            total_weight_44_ = 0
            total_weight_45_ = 0
            total_weight_46_ = 0
            total_weight_47_ = 0
            # filtered_datas = [line for line in report_data if line[48] == emp.id]
            for line in report_data:
                mrg_val = None 
                if line[2] != 'Strategic Projects' and line[2]:
                    total_weight_35_ += line[35]
                    total_weight_36_ += line[36]
                    total_weight_37_ += line[37]
                    total_weight_38_ += line[38]
                    total_weight_39_ += line[39]
                    total_weight_40_ += line[40]
                    total_weight_41_ += line[41]
                    total_weight_42_ += line[42]
                    total_weight_43_ += line[43]
                    total_weight_44_ += line[44]
                    total_weight_45_ += line[45]
                    total_weight_46_ += line[46]
                    total_weight_47_ += line[47]
                    if line[48] == emp.id:
                        slnumber += 1
                        col=0
                        line.pop(48)
                        if line[1]:
                            worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                            worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                            worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                            worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                            worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                            worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                        
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, l, report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                                # total_sum += l
                        elif col == 19 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 19 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1

                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_35_/100, report_column_style_)
            worksheet.write(row, 8, total_weight_36_/100, report_column_style_)
            worksheet.write(row, 9, total_weight_37_/100, report_column_style_)
            worksheet.write(row, 10, total_weight_38_/100, report_column_style_)
            worksheet.write(row, 11, total_weight_39_/100, report_column_style_)
            worksheet.write(row, 12, total_weight_40_/100, report_column_style_)
            worksheet.write(row, 13, total_weight_41_/100, report_column_style_)
            worksheet.write(row, 14, total_weight_42_/100, report_column_style_)
            worksheet.write(row, 15, total_weight_43_/100, report_column_style_)
            worksheet.write(row, 16, total_weight_44_/100, report_column_style_)
            worksheet.write(row, 17, total_weight_45_/100, report_column_style_)
            worksheet.write(row, 18, total_weight_46_/100, report_column_style_)
            worksheet.write(row, 19, total_weight_47_/100, report_column_style_)
            row+=1
            
            worksheet.merge_range(row, 0, row, 19, 'Strategic Projects', merge_format_)
            row+=1

            total_weight_35_l = 0
            total_weight_36_l = 0
            total_weight_37_l = 0
            total_weight_38_l = 0
            total_weight_39_l = 0
            total_weight_40_l = 0
            total_weight_41_l = 0
            total_weight_42_l = 0
            total_weight_43_l = 0
            total_weight_44_l = 0
            total_weight_45_l = 0
            total_weight_46_l = 0
            total_weight_47_l = 0
            # raise UserError((row,col))
            # filtered_datass = [line for line in report_data if line[48] == emp.id]
            for line in report_data:
                mrg_val = None
                if line[2] == 'Strategic Projects':
                    total_weight_35_l += line[35]
                    total_weight_36_l += line[36]
                    total_weight_37_l += line[37]
                    total_weight_38_l += line[38]
                    total_weight_39_l += line[39]
                    total_weight_40_l += line[40]
                    total_weight_41_l += line[41]
                    total_weight_42_l += line[42]
                    total_weight_43_l += line[43]
                    total_weight_44_l += line[44]
                    total_weight_45_l += line[45]
                    total_weight_46_l += line[46]
                    total_weight_47_l += line[47]
                    if line[48] == emp.id:
                        
                        slnumber += 1
                        col=0
                        line.pop(48)
                        if line[1]:
                            worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                            worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                            worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                            worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                            worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                            worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, l, report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,10,11,12,13,14,15,16,17,18)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                                # total_sum += l
                        elif col == 19 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 19 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1

                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_35_l/100, report_column_style_)
            worksheet.write(row, 8, total_weight_36_l/100, report_column_style_)
            worksheet.write(row, 9, total_weight_37_l/100, report_column_style_)
            worksheet.write(row, 10, total_weight_38_l/100, report_column_style_)
            worksheet.write(row, 11, total_weight_39_l/100, report_column_style_)
            worksheet.write(row, 12, total_weight_40_l/100, report_column_style_)
            worksheet.write(row, 13, total_weight_41_l/100, report_column_style_)
            worksheet.write(row, 14, total_weight_42_l/100, report_column_style_)
            worksheet.write(row, 15, total_weight_43_l/100, report_column_style_)
            worksheet.write(row, 16, total_weight_44_l/100, report_column_style_)
            worksheet.write(row, 17, total_weight_45_l/100, report_column_style_)
            worksheet.write(row, 18, total_weight_46_l/100, report_column_style_)
            worksheet.write(row, 19, total_weight_47_l/100, report_column_style_)
            row+=1
            
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('%s - Scorecard Quarterly'% (emp.department_id.parent_id.name if data.get('department_id') else emp.name))),
            'target': 'self',
        }
    

    def scorequarter_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
#         if data.get('date_from'):
#             domain.append(('date_from', '=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))   
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.parent_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append(('code', '=', 'NET'))
        
        # raise UserError((domain))
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        # raise UserError((docs1))
        # if docs1.filtered(lambda x: x.employee_id.company_id.id == 1):
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        # elif docs1.filtered(lambda x: x.employee_id.company_id.id == 3):
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        # else:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        
        # docs = docs2 | docs1
        #raise UserError((docs.id))
        docs = None
        datefrom = data.get('date_from')
        dateto = data.get('date_to')

        emply = docs1.mapped('employee_id')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        for emp in emply:
            if emp.company_id.id == 1:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Zipper','$ PAT (Thousand) - Zipper')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            elif emp.company_id.id == 3:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Metal Trims','$ PAT (Thousand) - Metal Trims')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            else:
                docs2 = self.env['hr.appraisal.goal'].search([('name', 'in', ('$ Revenue (Thousand)  - Zipper','$ PAT (Thousand) - Zipper','$ Revenue (Thousand)  - Metal Trims','$ PAT (Thousand) - Metal Trims')), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
            
            docs = docs2 | docs1.filtered(lambda x: x.employee_id.id == emp.id)   
            
            report_data = []
            emp_data = []
            slnumber=0
            for edata in docs:
                slnumber = slnumber+1
                emp_data = [
                    slnumber,
                    edata.name,
                    edata.description,
                    round(edata.baseline,2),
                    round(edata.target,2),
                    (edata.weight/100),
                    'Target',
                    edata.t_apr,
                    edata.t_may,
                    edata.t_jun,
                    edata.t_q1,
                    edata.t_jul,
                    edata.t_aug,
                    edata.t_sep,
                    edata.t_q2,
                    edata.t_oct,
                    edata.t_nov,
                    edata.t_dec,
                    edata.t_q3,
                    edata.t_jan,
                    edata.t_feb,
                    edata.t_mar,
                    edata.t_q4,
                    edata.y_t_ytd,
                    'ACVD',
                    edata.a_apr,
                    edata.a_may,
                    edata.a_jun,
                    edata.a_q1,
                    edata.a_jul,
                    edata.a_aug,
                    edata.a_sep,
                    edata.a_q2,
                    edata.a_oct,
                    edata.a_nov,
                    edata.a_dec,
                    edata.a_q3,
                    edata.a_jan,
                    edata.a_feb,
                    edata.a_mar,
                    edata.a_q4,
                    edata.y_a_ytd,
                    'Weightage',
                    edata.apr,
                    edata.may,
                    edata.jun,
                    edata.q_1_ytd,
                    edata.jul,
                    edata.aug,
                    edata.sep,
                    edata.q_2_ytd,
                    edata.oct,
                    edata.nov,
                    edata.dec,
                    edata.q_3_ytd,
                    edata.jan,
                    edata.feb,
                    edata.mar,
                    edata.q_4_ytd,
                    edata.y_ytd,
                    edata.employee_id.id,
                ]
                report_data.append(emp_data)
            month = docs.mapped('month')[1:]
            mm = 'Month'
            for m in month:
                if m == 'apr':
                    mm = 'April'
                elif m == 'may':
                    mm = 'May'
                elif m == 'jun':
                    mm = 'Jun'
                elif m == 'jul':
                    mm = 'July'
                elif m == 'aug':
                    mm = 'August'
                elif m == 'sep':
                    mm = 'September'
                elif m == 'oct':
                    mm = 'October'
                elif m == 'nov':
                    mm = 'November'
                elif m == 'dec':
                    mm = 'December'
                elif m == 'jan':
                    mm = 'January'
                elif m == 'feb':
                    mm = 'February'
                elif m == 'mar':
                    mm = 'March'
            weight = 0
            apr = 0
            may = 0
            jun = 0
            q_1_ytd = 0
            jul = 0
            aug = 0
            sep = 0
            q_2_ytd = 0
            oct = 0
            nov = 0
            dec = 0
            q_3_ytd = 0
            jan = 0
            feb = 0
            mar = 0
            q_4_ytd = 0  
            ytd = 0
            for de in docs1.filtered(lambda x: x.employee_id.id == emp.id):
                weight = weight + de.weight
                apr = apr + de.apr
                may = may + de.may
                jun = jun + de.jun
                q_1_ytd = q_1_ytd + de.q_1_ytd
                jul = jul + de.jul
                aug = aug + de.aug
                sep = sep + de.sep
                q_2_ytd = q_2_ytd + de.q_2_ytd
                oct = oct + de.oct
                nov = nov + de.nov
                dec = dec + de.dec
                q_3_ytd = q_3_ytd + de.q_3_ytd
                jan = jan + de.jan
                feb = feb + de.feb
                mar = mar + de.mar
                q_4_ytd = q_4_ytd + de.q_4_ytd
                ytd = ytd + de.y_ytd
                
            
            worksheet = workbook.add_worksheet(('%s - %s' % (emp.pin,emp.name)))
            worksheet.set_zoom(64)
            report_title_style = workbook.add_format({'align': 'center','bold': True, 'font_size': 16, 'bg_color': '#343A40','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_title_style1 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'font_size': 13, 'bg_color': '#343A40','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_column_style = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12})
            report_column_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12,'bold': True,'font_color':'#FFFFFF','bg_color': '#714B35', 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00%'})
            report_column_style_2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00'})
           
            report_column_style_2.set_text_wrap()
            report_column_style_3 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True, 'num_format': '0.00%'})
            worksheet.merge_range('A1:E1',('%s' % (emp.name)), report_title_style)
            
            # img = io.BytesIO(base64.b64decode(emp.image_1920))
            # worksheet.insert_image(0, 1, '', {'image_data': img, "x_scale": 0.06, "y_scale": 0.06,'align': 'center','valign': 'vcenter' })
            
            # img_ = io.BytesIO(base64.b64decode(emp.parent_id.image_1920))
            # worksheet.insert_image(0, 23, '', {'image_data': img_, "x_scale": 0.3, "y_scale": 0.3, 'object_position': 1})
            
            worksheet.merge_range('F1:M1', 'KPI Scorecard Quarterly [Challenged By]', report_title_style)
            worksheet.merge_range('N1:X1', ('%s' % (emp.parent_id.name)), report_title_style)
    
            report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14, 'border': True,'num_format': '0.00%'})
    #         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
            worksheet.merge_range('A2:E2',('%s' % (emp.job_title)), report_title_style1)
            worksheet.merge_range('F2:M2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_title_style1)
            worksheet.merge_range('N2:X2', ('%s' % (emp.parent_id.job_title)), report_title_style1)
            # worksheet.merge_range('C3:F3', ('KPI objective'), report_small_title_style)
            # worksheet.merge_range('A4:F4', ('%s - %s' % (emp.pin,emp.name)), report_title_style)
            worksheet.merge_range('F4:F4', "",report_title_style)
            # worksheet.merge_range('I4:L4', ('Weekly Plan'), report_title_style)
    #         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
            merge_format = workbook.add_format({'align': 'center','valign': 'vcenter', 'left': True, 'top': True, 'right': True, 'bottom': True})
            merge_format.set_text_wrap()
            merge_format_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 16, 'font_color':'#FFFFFF'})
            merge_format_.set_text_wrap()
            
            column_product_style = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            column_product_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B35', 'font_size': 14, 'font_color':'#FFFFFF', 'border': True})
            column_product_style2 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True})
            column_product_style_3 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00%'})
            column_product_style_5 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#714B62', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            column_product_style_6 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#343A40', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            
            column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12, 'border': True})
            column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12, 'border': True})
            row_categ_style = workbook.add_format({'border': True})
            gray_style = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            gray_style_ = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 16, 'font_color':'#FFFFFF', 'border': True, 'num_format': '0.00'})
            gray_style_1 = workbook.add_format({'align': 'center','valign': 'vcenter','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True,"num_format": "0.00%"})
    
            # set the width od the column
            percent_format = workbook.add_format({"num_format": "0%"})
            worksheet.freeze_panes(6, 0)
    
            
            worksheet.write(2, 2, 'WEIGHT', column_product_style_6)
            worksheet.write(2, 3, 'APR', column_product_style_6)
            worksheet.write(2, 4, 'MAY', column_product_style_6)
            worksheet.write(2, 5, 'JUN', column_product_style_6)
            worksheet.write(2, 6, 'Q1', gray_style_)
            worksheet.write(2, 7, 'JUL', column_product_style_6)
            worksheet.write(2, 8, 'AUG', column_product_style_6)
            worksheet.write(2, 9,  'SEP', column_product_style_6)
            worksheet.write(2, 10, 'Q2', gray_style_)
            worksheet.write(2, 11, 'OCT', column_product_style_6)
            worksheet.write(2, 12, 'NOV', column_product_style_6)
            worksheet.write(2, 13, 'DEC', column_product_style_6)
            worksheet.write(2, 14, 'Q3', gray_style_)
            worksheet.write(2, 15, 'JAN', column_product_style_6)
            worksheet.write(2, 16, 'FEB', column_product_style_6)
            worksheet.write(2, 17, 'MAR', column_product_style_6)
            worksheet.write(2, 18, 'Q4', gray_style_)
            worksheet.write(2, 19, 'YTD', column_product_style_5)
             
            
            worksheet.write(3, 2, weight, column_product_style_6)
            worksheet.write(3, 3, apr, column_product_style_6)
            worksheet.write(3, 4, may, column_product_style_6)
            worksheet.write(3, 5, jun, column_product_style_6)
            worksheet.write(3, 6, q_1_ytd, gray_style_)
            worksheet.write(3, 7, jul, column_product_style_6)
            worksheet.write(3, 8, aug, column_product_style_6)
            worksheet.write(3, 9, sep, column_product_style_6)
            worksheet.write(3, 10, q_2_ytd, gray_style_)
            worksheet.write(3, 11, oct, column_product_style_6)
            worksheet.write(3, 12, nov, column_product_style_6)
            worksheet.write(3, 13, dec, column_product_style_6)
            worksheet.write(3, 14, q_3_ytd, gray_style_)
            worksheet.write(3, 15, jan, column_product_style_6)
            worksheet.write(3, 16, feb, column_product_style_6)
            worksheet.write(3, 17, mar, column_product_style_6)
            worksheet.write(3, 18, q_4_ytd, gray_style_)
            worksheet.write(3, 19, ytd, column_product_style_5)
            # raise UserError((weight + de.weight))
            
            worksheet.set_column(0,0,3)
            worksheet.set_column(1,1,50)
            worksheet.set_column(2,2,20)
            worksheet.set_column(3,4,8)
            worksheet.set_column(5,5,10.20)
            worksheet.set_column(6,6,11)
            worksheet.set_column(23,23,11)
            
            worksheet.set_row(0, 20)
            
            worksheet.write(5, 0, 'SL.', column_product_style)
            worksheet.write(5, 1, 'Objectives', column_product_style)
            worksheet.write(5, 2, 'Description', column_product_style)
            worksheet.write(5, 3, 'Baseline', column_product_style)
            worksheet.write(5, 4, 'Target', column_product_style)
            worksheet.write(5, 5, 'Weight', column_product_style)
            worksheet.write(5, 6, 'Particulars', column_product_style)
            worksheet.write(5, 7, 'Apr', column_product_style)
            worksheet.write(5, 8, 'May', column_product_style)
            worksheet.write(5, 9, 'Jun', column_product_style)
            worksheet.write(5, 10,'Q1', column_product_style)
            worksheet.write(5, 11, 'Jul', column_product_style)
            worksheet.write(5, 12, 'Aug', column_product_style)
            worksheet.write(5, 13, 'Sep', column_product_style)
            worksheet.write(5, 14, 'Q2', column_product_style)
            worksheet.write(5, 15, 'Oct', column_product_style)
            worksheet.write(5, 16, 'Nov', column_product_style)
            worksheet.write(5, 17, 'Dec', column_product_style)
            worksheet.write(5, 18,'Q3', column_product_style)
            worksheet.write(5, 19, 'Jan', column_product_style)
            worksheet.write(5, 20, 'Feb', column_product_style)
            worksheet.write(5, 21, 'Mar', column_product_style)
            worksheet.write(5, 22, 'Q4', column_product_style)
            worksheet.write(5, 23, 'YTD', column_product_style)
            col = 0
            row=6
            grandtotal = 0
            slnumber = 0
            total_weight_43 = 0
            total_weight_44 = 0
            total_weight_45 = 0
            total_weight_46 = 0
            total_weight_47 = 0
            total_weight_48 = 0
            total_weight_49 = 0
            total_weight_50 = 0
            total_weight_51 = 0
            total_weight_52 = 0
            total_weight_53 = 0
            total_weight_54 = 0
            total_weight_55 = 0
            total_weight_56 = 0
            total_weight_57 = 0
            total_weight_58 = 0
            total_weight_59 = 0
            # worksheet.set_row(8, 35)
            worksheet.merge_range(row, 0, row, 23, 'Revenue & PAT', merge_format_)
            row=7
            
            for line in report_data:
                mrg_val = None    
                if not line[60]:
                    total_weight_43 += line[43]
                    total_weight_44 += line[44]
                    total_weight_45 += line[45]
                    total_weight_46 += line[46]
                    total_weight_47 += line[47]
                    total_weight_48 += line[48]
                    total_weight_49 += line[49]
                    total_weight_50 += line[50]
                    total_weight_51 += line[51]
                    total_weight_52 += line[52]
                    total_weight_53 += line[53]
                    total_weight_54 += line[54]
                    total_weight_55 += line[55]
                    total_weight_56 += line[56]
                    total_weight_57 += line[57]
                    total_weight_58 += line[58]
                    total_weight_59 += line[59]
                    slnumber += 1
                    col=0
                    line.pop(60)
                    if line[1]:
                        worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                        worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                        worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                        worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                        worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                        worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                        # worksheet.write(sum(row, 0, row[2], 0, l, merge_format))
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, '', report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                            
                        elif (col in (10,14,18,22)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, gray_style_1)
                        
                        elif (col in (10,14,18,22)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, gray_style)
                                # total_sum += l
                        elif col == 23 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 23 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1
    
                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_43/100, report_column_style_)
            worksheet.write(row, 8, total_weight_44/100, report_column_style_)
            worksheet.write(row, 9, total_weight_45/100, report_column_style_)
            worksheet.write(row, 10, total_weight_46/100, gray_style_1)
            worksheet.write(row, 11, total_weight_47/100, report_column_style_)
            worksheet.write(row, 12, total_weight_48/100, report_column_style_)
            worksheet.write(row, 13, total_weight_49/100, report_column_style_)
            worksheet.write(row, 14, total_weight_50/100, gray_style_1)
            worksheet.write(row, 15, total_weight_51/100, report_column_style_)
            worksheet.write(row, 16, total_weight_52/100, report_column_style_)
            worksheet.write(row, 17, total_weight_53/100, report_column_style_)
            worksheet.write(row, 18, total_weight_54/100, gray_style_1)
            worksheet.write(row, 19, total_weight_55/100, report_column_style_)
            worksheet.write(row, 20, total_weight_56/100, report_column_style_)
            worksheet.write(row, 21, total_weight_57/100, report_column_style_)
            worksheet.write(row, 22, total_weight_58/100, gray_style_1)
            worksheet.write(row, 23, total_weight_59/100, report_column_style_)
            row+=1
            
                    
            worksheet.merge_range(row, 0, row, 23, 'Objective / Score', merge_format_)
            row+=1
    
            total_weight_43_ = 0
            total_weight_44_ = 0
            total_weight_45_ = 0
            total_weight_46_ = 0
            total_weight_47_ = 0
            total_weight_48_ = 0
            total_weight_49_ = 0
            total_weight_50_ = 0
            total_weight_51_ = 0
            total_weight_52_ = 0
            total_weight_53_ = 0
            total_weight_54_ = 0
            total_weight_55_ = 0
            total_weight_56_ = 0
            total_weight_57_ = 0
            total_weight_58_ = 0
            total_weight_59_ = 0
            for line in report_data:
                mrg_val = None 
                if line[2] != 'Strategic Projects' and line[2]:
                    total_weight_43_ += line[43]
                    total_weight_44_ += line[44]
                    total_weight_45_ += line[45]
                    total_weight_46_ += line[46]
                    total_weight_47_ += line[47]
                    total_weight_48_ += line[48]
                    total_weight_49_ += line[49]
                    total_weight_50_ += line[50]
                    total_weight_51_ += line[51]
                    total_weight_52_ += line[52]
                    total_weight_53_ += line[53]
                    total_weight_54_ += line[54]
                    total_weight_55_ += line[55]
                    total_weight_56_ += line[56]
                    total_weight_57_ += line[57]
                    total_weight_58_ += line[58]
                    total_weight_59_ += line[59]
                    if line[60] == emp.id:
                        slnumber += 1
                        col=0
                        line.pop(60)
                        if line[1]:
                            worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                            worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                            worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                            worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                            worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                            worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                        
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, l, report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                            
                        elif (col in (10,14,18,22)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, gray_style_1)
                        
                        elif (col in (10,14,18,22)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, gray_style)
                                # total_sum += l
                        elif col == 23 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 23 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1
    
                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_43_/100, report_column_style_)
            worksheet.write(row, 8, total_weight_44_/100, report_column_style_)
            worksheet.write(row, 9, total_weight_45_/100, report_column_style_)
            worksheet.write(row, 10, total_weight_46_/100, gray_style_1)
            worksheet.write(row, 11, total_weight_47_/100, report_column_style_)
            worksheet.write(row, 12, total_weight_48_/100, report_column_style_)
            worksheet.write(row, 13, total_weight_49_/100, report_column_style_)
            worksheet.write(row, 14, total_weight_50_/100, gray_style_1)
            worksheet.write(row, 15, total_weight_51_/100, report_column_style_)
            worksheet.write(row, 16, total_weight_52_/100, report_column_style_)
            worksheet.write(row, 17, total_weight_53_/100, report_column_style_)
            worksheet.write(row, 18, total_weight_54_/100, gray_style_1)
            worksheet.write(row, 19, total_weight_55_/100, report_column_style_)
            worksheet.write(row, 20, total_weight_56_/100, report_column_style_)
            worksheet.write(row, 21, total_weight_57_/100, report_column_style_)
            worksheet.write(row, 22, total_weight_58_/100, gray_style_1)
            worksheet.write(row, 23, total_weight_59_/100, report_column_style_)
            row+=1
            
            worksheet.merge_range(row, 0, row, 23, 'Strategic Projects', merge_format_)
            row+=1
    
            total_weight_43_l = 0
            total_weight_44_l = 0
            total_weight_45_l = 0
            total_weight_46_l = 0
            total_weight_47_l = 0
            total_weight_48_l = 0
            total_weight_49_l = 0
            total_weight_50_l = 0
            total_weight_51_l = 0
            total_weight_52_l = 0
            total_weight_53_l = 0
            total_weight_54_l = 0
            total_weight_55_l = 0
            total_weight_56_l = 0
            total_weight_57_l = 0
            total_weight_58_l = 0
            total_weight_59_l = 0
            # raise UserError((row,col))
            for line in report_data:
                mrg_val = None 
                if line[2] == 'Strategic Projects':
                    total_weight_43_l += line[43]
                    total_weight_44_l += line[44]
                    total_weight_45_l += line[45]
                    total_weight_46_l += line[46]
                    total_weight_47_l += line[47]
                    total_weight_48_l += line[48]
                    total_weight_49_l += line[49]
                    total_weight_50_l += line[50]
                    total_weight_51_l += line[51]
                    total_weight_52_l += line[52]
                    total_weight_53_l += line[53]
                    total_weight_54_l += line[54]
                    total_weight_55_l += line[55]
                    total_weight_56_l += line[56]
                    total_weight_57_l += line[57]
                    total_weight_58_l += line[58]
                    total_weight_59_l += line[59]
                    if line[60] == emp.id:
                        
                        slnumber += 1
                        col=0
                        line.pop(60)
                        if line[1]:
                            worksheet.merge_range(row, 0, row+2, 0, '', merge_format)
                            worksheet.merge_range(row, 1, row+2, 1, '', merge_format)
                            worksheet.merge_range(row, 2, row+2, 2, '', merge_format)
                            worksheet.merge_range(row, 3, row+2, 3, '', merge_format)
                            worksheet.merge_range(row, 4, row+2, 4, '', merge_format)
                            worksheet.merge_range(row, 5, row+2, 5, '', merge_format)
                    wei = None
                    for l in line:
                        # len (line)
                        # if line[6] == 'Weightage':
                        #     raise UserError(('fefefgrgr'))
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style)
                        if col == 1:
                            worksheet.write(row, col, l, report_column_style_2)
                        if col == 2:
                            worksheet.write(row, col, l, report_column_style_2)
                        elif col == 3:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 4:
                            
                            if etype == '%':
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col == 6:
                            wei = l
                            worksheet.write(row, col, l, column_product_style)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, report_column_style_3)
                        
                        elif (col in (7,8,9,11,12,13,15,16,17,19,20,21)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, report_column_style_2)
                            
                        elif (col in (10,14,18,22)) and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, gray_style_1)
                        
                        elif (col in (10,14,18,22)) and (wei != 'Weightage'):
                            worksheet.write(row, col, l, gray_style)
                                # total_sum += l
                        elif col == 23 and (wei == 'Weightage'):
                            worksheet.write(row, col, l/100, column_product_style_3)
                            row+=1
                            col=5
                        elif col == 23 and (wei != 'Weightage'):
                            worksheet.write(row, col, l, column_product_style)
                            row+=1
                            col=5
                        elif col==5:
                            # grandtotal = grandtotal+l
                            worksheet.write(row, col, l, report_column_style_3)
                            
                        col+=1
    
                    row = row-1
                    row+=1
            worksheet.write(row, 6, 'Total', column_product_style_)
            worksheet.write(row, 7, total_weight_43_l/100, report_column_style_)
            worksheet.write(row, 8, total_weight_44_l/100, report_column_style_)
            worksheet.write(row, 9, total_weight_45_l/100, report_column_style_)
            worksheet.write(row, 10, total_weight_46_l/100, gray_style_1)
            worksheet.write(row, 11, total_weight_47_l/100, report_column_style_)
            worksheet.write(row, 12, total_weight_48_l/100, report_column_style_)
            worksheet.write(row, 13, total_weight_49_l/100, report_column_style_)
            worksheet.write(row, 14, total_weight_50_l/100, gray_style_1)
            worksheet.write(row, 15, total_weight_51_l/100, report_column_style_)
            worksheet.write(row, 16, total_weight_52_l/100, report_column_style_)
            worksheet.write(row, 17, total_weight_53_l/100, report_column_style_)
            worksheet.write(row, 18, total_weight_54_l/100, gray_style_1)
            worksheet.write(row, 19, total_weight_55_l/100, report_column_style_)
            worksheet.write(row, 20, total_weight_56_l/100, report_column_style_)
            worksheet.write(row, 21, total_weight_57_l/100, report_column_style_)
            worksheet.write(row, 22, total_weight_58_l/100, gray_style_1)
            worksheet.write(row, 23, total_weight_59_l/100, report_column_style_)
            row+=1
            
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('%s - Scorecard Quarterly'% (emp.department_id.parent_id.name if data.get('department_id') else emp.name))),
            'target': 'self',
        }


    def kpi_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()
        domain = []
#         if data.get('date_from'):
#             domain.append(('date_from', '=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))   
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.parent_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append(('code', '=', 'NET'))
        
        # raise UserError((domain))
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        # if docs1.employee_id.company_id.id == 1:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27))]).sorted(key = 'id', reverse=False)
        # elif docs1.employee_id.company_id.id == 3:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28))]).sorted(key = 'id', reverse=False)
        # else:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28))]).sorted(key = 'id', reverse=False)
        
        docs = docs1
        #raise UserError((docs.id))
        datefrom = data.get('date_from')
        dateto = data.get('date_to')
#         bankname = self.bank_id.name
#         categname=[]
#         if self.employee_type =='staff':
#             categname='Staffs'
#         if self.employee_type =='expatriate':
#             categname='Expatriates'
#         if self.employee_type =='worker':
#             categname='Workers'
#         if self.employee_type =='cstaff':
#             categname='C-Staffs'
#         if self.employee_type =='cworker':
#             categname='C-Workers'
            
        
        #raise UserError((datefrom,dateto,bankname,categname))
        report_data = []
        emp_data = []
        slnumber=0
        for edata in docs:
            slnumber = slnumber+1
            emp_data = [
                slnumber,
                edata.name,
                edata.description,
                round(edata.baseline,2),
                round(edata.target,2),
                (edata.weight/100),
                edata.employee_id.id,
            ]
            report_data.append(emp_data)     
        emply = docs.mapped('employee_id')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # raise UserError((emply))
        for emp in emply:
            
            worksheet = workbook.add_worksheet(('%s - %s' % (emp.pin,emp.name)))
            report_title_style = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#714B62','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_column_style = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12})
            report_column_style_2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True})
            report_column_style_2.set_text_wrap()
            report_column_style_3 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True,'num_format': '0.00%'})
            worksheet.merge_range('A1:F1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
    
            report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14, 'border': True,'num_format': '0.00%'})
    #         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
            worksheet.merge_range('A2:F2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
            worksheet.merge_range('A3:F3', ('KPI objective'), report_small_title_style)
            worksheet.merge_range('A4:F4', ('%s - %s' % (emp.pin,emp.name)), report_title_style)
            worksheet.merge_range('F4:F4', "",report_title_style)
            # worksheet.merge_range('I4:L4', ('Weekly Plan'), report_title_style)
    #         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
            
            column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True})
            column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12, 'border': True})
            column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12, 'border': True})
            row_categ_style = workbook.add_format({'border': True})
    
            # set the width od the column
            
            percent_format = workbook.add_format({"num_format": "0%"})
            worksheet.freeze_panes(5, 0)
    
            
            worksheet.set_column(0,0,3)
            worksheet.set_column(1,1,50)
            worksheet.set_column(2,2,20)
            worksheet.set_column(3,4,8)
            worksheet.set_column(5,5,9.44)
            
            
            
            worksheet.write(4, 0, 'SL.', column_product_style)
            worksheet.write(4, 1, 'Objectives', column_product_style)
            worksheet.write(4, 2, 'Description', column_product_style)
            worksheet.write(4, 3, 'Baseline', column_product_style)
            worksheet.write(4, 4, 'Target', column_product_style)
            worksheet.write(4, 5, 'Weight', column_product_style)
            col = 0
            row=5
            
            grandtotal = 0
    #         grandtotal2 = 0
    #         grandtotal3 = 0
            
            slnumber = 0
            for line in report_data:
                # raise UserError((line[8],emp.id))
                # slnumber=0
                
                # raise UserError((line[2],emp.id))
                if line[2] != 'Strategic Projects' and line[2]:
                    if line[6] == emp.id:
                        slnumber += 1
                        col=0
                        for l in line:
                            if col == 1:
                                etype = l[:1]
                            if col == 0:
                                worksheet.write(row, col, slnumber, report_column_style_2) 
                            if col == 1:
                                worksheet.write(row, col, l, report_column_style_2) 
                            if col == 2:
                                worksheet.write(row, col, l, report_column_style_2) 
                            elif col == 3:
                                
                                if etype == '%':
                                    # raise UserError((etype))
                                    ld = l/100
                                    worksheet.write(row, col, ld, report_column_style_3)
                                else:
                                    # raise UserError((etype))
                                    worksheet.write(row, col, l, report_column_style_2)                    
                            elif col == 4:
                                
                                if etype == '%':
                                    # raise UserError((etype))
                                    ld = l/100
                                    worksheet.write(row, col, ld, report_column_style_3)
                                else:
                                    # raise UserError((etype))
                                    worksheet.write(row, col, l, report_column_style_2)
                            elif col==5:
                                grandtotal = grandtotal+l
                                # format = workbook.add_format({'num_format': num_formats})
                                worksheet.write(row, col, l, report_column_style_3)
                            # elif col==8:
                            #     break
                            # else:
                            #     worksheet.write(row, col, l, report_column_style_2)
                            col+=1
                        row+=1
                    worksheet.write(row, 0, '', report_small_title_style)
                    worksheet.write(row, 1, 'Total', report_small_title_style)
                    worksheet.write(row, 2, '', report_small_title_style)
                    worksheet.write(row, 3, '', report_small_title_style)
                    worksheet.write(row, 4, '', report_small_title_style)
                    worksheet.write(row, 5, round(grandtotal,2), report_small_title_style)
            row+=1            
            worksheet.merge_range(row, 0, row, 5, 'Strategic Projects', column_product_style)
            row+=1 
            grandtotal_ = 0
            for line in report_data:       
                if line[2] == 'Strategic Projects':
                    # raise UserError(("hi"))
                    if line[6] == emp.id:
                        slnumber += 1
                        col=0
                        for l in line:
                            if col == 1:
                                etype = l[:1]
                            if col == 0:
                                worksheet.write(row, col, slnumber, report_column_style_2) 
                            if col == 1:
                                worksheet.write(row, col, l, report_column_style_2) 
                            if col == 2:
                                worksheet.write(row, col, l, report_column_style_2) 
                            elif col == 3:
                                
                                if etype == '%':
                                    # raise UserError((etype))
                                    ld = l/100
                                    worksheet.write(row, col, ld, report_column_style_3)
                                else:
                                    # raise UserError((etype))
                                    worksheet.write(row, col, l, report_column_style_2)                    
                            elif col == 4:
                                
                                if etype == '%':
                                    # raise UserError((etype))
                                    ld = l/100
                                    worksheet.write(row, col, ld, report_column_style_3)
                                else:
                                    # raise UserError((etype))
                                    worksheet.write(row, col, l, report_column_style_2)
                            elif col==5:
                                grandtotal_ = grandtotal_+l
                                # format = workbook.add_format({'num_format': num_formats})
                                worksheet.write(row, col, l, report_column_style_3)
                            # elif col==8:
                            #     break
                            # else:
                            #     worksheet.write(row, col, l, report_column_style_2)
                            col+=1
                        row+=1
                                        
                
                        
            
                    #worksheet.write(4, 0, 'SL.', column_product_style)
                    
                    worksheet.write(row, 0, '', report_small_title_style)
                    worksheet.write(row, 1, 'Total', report_small_title_style)
                    worksheet.write(row, 2, '', report_small_title_style)
                    worksheet.write(row, 3, '', report_small_title_style)
                    worksheet.write(row, 4, '', report_small_title_style)
                    worksheet.write(row, 5, round(grandtotal_,2), report_small_title_style)

                    
                    #raise UserError((datefrom,dateto,bankname,categname))
            
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('%s - KPI objective'% (emp.department_id.parent_id.name))),
            'target': 'self',
        }

            
    def plan_xls_template(self, docids, data=None):
        start_time = fields.datetime.now()        
        domain = []
#         if data.get('date_from'):
#             domain.append(('date_from', '=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))   
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.parent_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append(('code', '=', 'NET'))
        
        #raise UserError((domain))
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        # if docs1.employee_id.company_id.id == 1:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27))]).sorted(key = 'id', reverse=False)
        # elif docs1.employee_id.company_id.id == 3:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28))]).sorted(key = 'id', reverse=False)
        # else:
        #     docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28))]).sorted(key = 'id', reverse=False)
        
        docs = docs1
        #raise UserError((docs.id))
        datefrom = data.get('date_from')
        dateto = data.get('date_to')
#         bankname = self.bank_id.name
#         categname=[]
#         if self.employee_type =='staff':
#             categname='Staffs'
#         if self.employee_type =='expatriate':
#             categname='Expatriates'
#         if self.employee_type =='worker':
#             categname='Workers'
#         if self.employee_type =='cstaff':
#             categname='C-Staffs'
#         if self.employee_type =='cworker':
#             categname='C-Workers'
            
        
        #raise UserError((datefrom,dateto,bankname,categname))
        report_data = []
        emp_data = []
        slnumber=0
        for edata in docs:
            slnumber = slnumber+1
            emp_data = [
                slnumber,
                edata.name,
                round(edata.baseline,2),
                round(edata.target,2),
                (edata.weight/100),
                "",
                "",
                "",
                edata.employee_id.id,
            ]
            report_data.append(emp_data)     
        emply = docs.mapped('employee_id')
        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        # raise UserError((emply))
        for emp in emply:
            
            worksheet = workbook.add_worksheet(('%s - %s' % (emp.pin,emp.name)))
            report_title_style = workbook.add_format({'bold': True, 'font_size': 16, 'bg_color': '#714B62','right': True, 'border': True, 'font_color':'#FFFFFF'})
            report_column_style = workbook.add_format({'align': 'center','valign': 'vcenter','font_size': 12})
            report_column_style_2 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True})
            report_column_style_2.set_text_wrap()
            report_column_style_3 = workbook.add_format({'align': 'left','valign': 'vcenter','font_size': 12, 'left': True, 'top': True, 'right': True, 'bottom': True,'num_format': '0.00%'})
            worksheet.merge_range('A1:H1', 'TEX ZIPPERS (BD) LIMITED', report_title_style)
    
            report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14, 'border': True,'num_format': '0.00%'})
    #         worksheet.write(1, 2, ('From %s to %s' % (datefrom,dateto)), report_small_title_style)
            worksheet.merge_range('A2:H2', (datetime.strptime(str(dateto), '%Y-%m-%d').strftime('%B  %Y')), report_small_title_style)
            worksheet.merge_range('A3:H3', ('KPI objective with Action Plan'), report_small_title_style)
            worksheet.merge_range('A4:E4', ('%s - %s' % (emp.pin,emp.name)), report_title_style)
            worksheet.merge_range('F4:H4', "",report_title_style)
            # worksheet.merge_range('I4:L4', ('Weekly Plan'), report_title_style)
    #         worksheet.write(2, 1, ('TZBD,%s EMPLOYEE %s TRANSFER LIST' % (categname,bankname)), report_small_title_style)
            
            column_product_style = workbook.add_format({'align': 'center','bold': True, 'bg_color': '#808080', 'font_size': 12, 'font_color':'#FFFFFF', 'border': True})
            column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12, 'border': True})
            column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12, 'border': True})
            row_categ_style = workbook.add_format({'border': True})
    
            # set the width od the column
            
            percent_format = workbook.add_format({"num_format": "0%"})
    
            
            worksheet.set_column(0,0,3)
            worksheet.set_column(1,1,50)
            worksheet.set_column(2,3,8)
            worksheet.set_column(4,4,9.44)
            worksheet.set_column(5,7,20)
            
            
            
            worksheet.write(4, 0, 'SL.', column_product_style)
            worksheet.write(4, 1, 'Objectives', column_product_style)        
            worksheet.write(4, 2, 'Baseline', column_product_style)
            worksheet.write(4, 3, 'Target', column_product_style)
            worksheet.write(4, 4, 'Weight', column_product_style)
            worksheet.write(4, 5, 'Last Month Achieved', column_product_style)
            worksheet.write(4, 6, 'Current Monthly Plan', column_product_style)
            worksheet.write(4, 7, 'Actions', column_product_style)
            col = 0
            row=5
            
            grandtotal = 0
    #         grandtotal2 = 0
    #         grandtotal3 = 0
            
            slnumber = 0
            for line in report_data:
                # raise UserError((line[8],emp.id))
                # slnumber=0
                
                
                
                if line[8] == emp.id:
                    slnumber += 1
                    col=0
                    for l in line:
                        if col == 1:
                            etype = l[:1]
                        if col == 0:
                            worksheet.write(row, col, slnumber, report_column_style_2)  
                        elif col == 2:
                            
                            if etype == '%':
                                # raise UserError((etype))
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                # raise UserError((etype))
                                worksheet.write(row, col, l, report_column_style_2)                    
                        elif col == 3:
                            
                            if etype == '%':
                                # raise UserError((etype))
                                ld = l/100
                                worksheet.write(row, col, ld, report_column_style_3)
                            else:
                                # raise UserError((etype))
                                worksheet.write(row, col, l, report_column_style_2)
                        elif col==4:
                            grandtotal = grandtotal+l
                            # format = workbook.add_format({'num_format': num_formats})
                            worksheet.write(row, col, l, report_column_style_3)
                        elif col==8:
                            break
                        else:
                            worksheet.write(row, col, l, report_column_style_2)
                        col+=1
                    row+=1
                    
            
                    #worksheet.write(4, 0, 'SL.', column_product_style)
                    #raise UserError((row+1))
                    worksheet.write(row, 0, '', report_small_title_style)
                    worksheet.write(row, 1, 'Grand Total', report_small_title_style)
                    worksheet.write(row, 2, '', report_small_title_style)
                    worksheet.write(row, 3, '', report_small_title_style)
                    worksheet.write(row, 4, round(grandtotal,2), report_small_title_style)
                    worksheet.write(row, 5, '', report_small_title_style)
                    worksheet.write(row, 6, '', report_small_title_style)
                    worksheet.write(row, 7, '', report_small_title_style)
                    #raise UserError((datefrom,dateto,bankname,categname))
            
        workbook.close()
        output.seek(0)
        xlsx_data = output.getvalue()
        #raise UserError(('sfrgr'))
        
        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, ('%s - KPI objective with Action Plan'% (emp.department_id.parent_id.name))),
            'target': 'self',
        }    


    

class KpiScoreReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.kpi_objective_score_pdf_template'
    _description = 'KPI Objective Score Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))
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
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             #str = re.sub("[^0-9]","",data.get('employee_id'))
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append( ('id', 'in', (25,26,27,28)))        
        
        
        
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        if docs1.employee_id.company_id.id == 1:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        elif docs1.employee_id.company_id.id == 3:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        else:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        
        docs = docs2 | docs1
#         raise UserError((docs.id))
        month = docs.mapped('month')[1:]
        mm = 'Month'
        for m in month:
            if m == 'apr':
                mm = 'April'
            elif m == 'may':
                mm = 'May'
            elif m == 'jun':
                mm = 'Jun'
            elif m == 'jul':
                mm = 'July'
            elif m == 'aug':
                mm = 'August'
            elif m == 'sep':
                mm = 'September'
            elif m == 'oct':
                mm = 'October'
            elif m == 'nov':
                mm = 'November'
            elif m == 'dec':
                mm = 'December'
            elif m == 'jan':
                mm = 'January'
            elif m == 'feb':
                mm = 'February'
            elif m == 'mar':
                mm = 'March'
        weight = 0
        apr = 0
        may = 0
        jun = 0
        jul = 0
        aug = 0
        sep = 0
        oct = 0
        nov = 0
        dec = 0
        jan = 0
        feb = 0
        mar = 0
        ytd = 0
        for de in docs1:
            weight = weight + de.weight
            apr = apr + de.apr
            may = may + de.may
            jun = jun + de.jun
            jul = jul + de.jul
            aug = aug + de.aug
            sep = sep + de.sep
            oct = oct + de.oct
            nov = nov + de.nov
            dec = dec + de.dec
            jan = jan + de.jan
            feb = feb + de.feb
            mar = mar + de.mar
            ytd = ytd + de.y_ytd
            
        common_data = [
            data.get('report_type'),
            mm,
            weight,
            apr,
            may,
            jun,
            jul,
            aug,
            sep,
            oct,
            nov,
            dec,
            jan,
            feb,
            mar,
            ytd,
#             round(otTotal),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
#         raise UserError((common_data[1]))
#         raise UserError((mm))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.appraisal.goal',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }

class KpiScoreQuaterReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.kpi_objective_score_quarter_pdf_template'
    _description = 'KPI Objective Score Quarterly Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))
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
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             #str = re.sub("[^0-9]","",data.get('employee_id'))
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append( ('id', 'in', (25,26,27,28)))        
        
        
        
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        if docs1.employee_id.company_id.id == 1:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        elif docs1.employee_id.company_id.id == 3:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        else:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        
        docs = docs2 | docs1
#         raise UserError((docs.id))
        month = docs.mapped('month')[1:]
        mm = 'Month'
        for m in month:
            if m == 'apr':
                mm = 'April'
            elif m == 'may':
                mm = 'May'
            elif m == 'jun':
                mm = 'Jun'
            elif m == 'jul':
                mm = 'July'
            elif m == 'aug':
                mm = 'August'
            elif m == 'sep':
                mm = 'September'
            elif m == 'oct':
                mm = 'October'
            elif m == 'nov':
                mm = 'November'
            elif m == 'dec':
                mm = 'December'
            elif m == 'jan':
                mm = 'January'
            elif m == 'feb':
                mm = 'February'
            elif m == 'mar':
                mm = 'March'
        weight = 0
        apr = 0
        may = 0
        jun = 0
        q_1_ytd = 0
        jul = 0
        aug = 0
        sep = 0
        q_2_ytd = 0
        oct = 0
        nov = 0
        dec = 0
        q_3_ytd = 0
        jan = 0
        feb = 0
        mar = 0
        q_4_ytd = 0  
        ytd = 0
        for de in docs1:
            weight = weight + de.weight
            apr = apr + de.apr
            may = may + de.may
            jun = jun + de.jun
            q_1_ytd = q_1_ytd + de.q_1_ytd
            jul = jul + de.jul
            aug = aug + de.aug
            sep = sep + de.sep
            q_2_ytd = q_2_ytd + de.q_2_ytd
            oct = oct + de.oct
            nov = nov + de.nov
            dec = dec + de.dec
            q_3_ytd = q_3_ytd + de.q_3_ytd
            jan = jan + de.jan
            feb = feb + de.feb
            mar = mar + de.mar
            q_4_ytd = q_4_ytd + de.q_4_ytd
            ytd = ytd + de.y_ytd
            
        common_data = [
            data.get('report_type'),
            mm,
            weight,
            apr,
            may,
            jun,
            jul,
            aug,
            sep,
            oct,
            nov,
            dec,
            jan,
            feb,
            mar,
            ytd,
#             round(otTotal),
            data.get('date_from'),
            data.get('date_to'),
            q_1_ytd,
            q_2_ytd,
            q_3_ytd,
            q_4_ytd,
        ]
        common_data.append(common_data)
#         raise UserError((common_data[1]))
#         raise UserError((mm))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.appraisal.goal',
            'docs': docs,
            'datas': common_data,
#             'alldays': all_datelist
        }

class KpiReportPDF(models.AbstractModel):
    _name = 'report.taps_hr.kpi_objective_pdf_template'
    _description = 'KPI Objective Report Template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        
#         if data.get('bank_id')==False:
#             domain.append(('code', '=', data.get('report_type')))
#         if data.get('date_from'):
#             domain.append(('date_from', '>=', data.get('date_from')))
#         if data.get('date_to'):
#             domain.append(('date_to', '<=', data.get('date_to')))
        if data.get('year'):
            deadlines = str(data.get('year') + '-03-31')
            domain.append(('deadline', '=', deadlines))
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
            domain.append(('employee_id.id', '=', data.get('employee_id')))
#         if data.get('bank_id'):
#             #str = re.sub("[^0-9]","",data.get('employee_id'))
#             domain.append(('employee_id.bank_account_id.bank_id', '=', data.get('bank_id')))
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
#         domain.append( ('id', 'in', (25,26,27,28)))        
        
        
        
        docs1 = self.env['hr.appraisal.goal'].search(domain).sorted(key = 'id', reverse=False)
        if docs1.employee_id.company_id.id == 1:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,27)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        elif docs1.employee_id.company_id.id == 3:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (26,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        else:
            docs2 = self.env['hr.appraisal.goal'].search([('id', 'in', (25,26,27,28)), ('deadline', '=', deadlines)]).sorted(key = 'id', reverse=False)
        
        docs = docs2 | docs1
#         raise UserError((docs.id))
        month = docs.mapped('month')[1:]
        mm = 'Month'
        for m in month:
            if m == 'apr':
                mm = 'April'
            elif m == 'may':
                mm = 'May'
            elif m == 'jun':
                mm = 'Jun'
            elif m == 'jul':
                mm = 'July'
            elif m == 'aug':
                mm = 'August'
            elif m == 'sep':
                mm = 'September'
            elif m == 'oct':
                mm = 'October'
            elif m == 'nov':
                mm = 'November'
            elif m == 'dec':
                mm = 'December'
            elif m == 'jan':
                mm = 'January'
            elif m == 'feb':
                mm = 'February'
            elif m == 'mar':
                mm = 'March'
        weight = 0
        apr = 0
        may = 0
        jun = 0
        jul = 0
        aug = 0
        sep = 0
        oct = 0
        nov = 0
        dec = 0
        jan = 0
        feb = 0
        mar = 0
        ytd = 0
        for de in docs1:
            weight = weight + de.weight
            apr = apr + de.apr
            may = may + de.may
            jun = jun + de.jun
            jul = jul + de.jul
            aug = aug + de.aug
            sep = sep + de.sep
            oct = oct + de.oct
            nov = nov + de.nov
            dec = dec + de.dec
            jan = jan + de.jan
            feb = feb + de.feb
            mar = mar + de.mar
            ytd = ytd + de.y_ytd
            
        common_data = [
            data.get('report_type'),
            mm,
            weight,
            apr,
            may,
            jun,
            jul,
            aug,
            sep,
            oct,
            nov,
            dec,
            jan,
            feb,
            mar,
            ytd,
#             round(otTotal),
            data.get('date_from'),
            data.get('date_to'),
        ]
        common_data.append(common_data)
#         raise UserError((common_data[1]))
#         raise UserError((mm))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.appraisal.goal',
            'docs': docs1,
            'datas': common_data,
#             'alldays': all_datelist
        }
