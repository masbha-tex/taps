# -*- coding:utf-8 -*-
import base64
from odoo import models, fields, api, _
from odoo.exceptions import UserError,ValidationError
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from odoo.addons.resource.models.resource_mixin import timezone_datetime
from odoo.addons.resource.models.resource import datetime_to_string, string_to_datetime, Intervals
from odoo.tools.float_utils import float_round
from odoo.tools import date_utils, float_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval
import math
import pytz

class HrPayslipsss(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Pay Slip'
    _order = 'emp_id'
    
    emp_id = fields.Char(related = 'employee_id.emp_id', related_sudo=False, string="Emp ID", readonly=True, store=True)
    department_id = fields.Many2one('hr.department', compute='_compute_employee_contract', store=True, readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string="Department")
    job_id = fields.Many2one('hr.job', compute='_compute_employee_contract', store=True, readonly=False,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", string='Job Position')    
    join_date = fields.Date(related = 'contract_id.date_start', related_sudo=False, string="Join Date", readonly=True, store=True)
    emp_type = fields.Selection(related = 'contract_id.category', related_sudo=False, string="Emp Type", readonly=True, store=True)
    com_otHours = fields.Float(string = "C-OT Hours", compute="_compute_ot_rate", store=True, copy=True) 
    otHours = fields.Float(string = "OT Hours", compute="_compute_ot_rate", store=True, copy=True)
    otRate = fields.Float(string = "OT Rate", compute="_compute_ot_rate", store=True, copy=True)
    gross_wage = fields.Monetary( store=True, copy=True, readonly=True)
    basic_wage = fields.Float( store=True, copy=True)
    hra_wage = fields.Float( store=True, copy=True)
    medical_wage = fields.Float( store=True, copy=True)
    ot_wage = fields.Float( store=True, copy=True)
    arrear_wage = fields.Float( store=True, copy=True)
    att_bonus_wage = fields.Float( store=True, copy=True)
    convence_wage = fields.Float( store=True, copy=True)
    food_wage = fields.Float( store=True, copy=True)
    tiffin_wage = fields.Float( store=True, copy=True)
    snacks_wage = fields.Float( store=True, copy=True)
    car_wage = fields.Float( store=True, copy=True)
    others_alw_wage = fields.Float( store=True, copy=True)
    incentive_wage = fields.Float( store=True, copy=True)
    pf_empr_wage = fields.Float( store=True, copy=True)
    pf_empe_wage = fields.Float( store=True, copy=True)
    rpf_wage = fields.Float( store=True, copy=True)
    ait_wage = fields.Float( store=True, copy=True)
    basic_absent_wage = fields.Float( store=True, copy=True)
    gross_absent_wage = fields.Float( store=True, copy=True)
    loan_wage = fields.Float( store=True, copy=True)
    adv_salary_wage = fields.Float( store=True, copy=True)
    others_ded_wage = fields.Float( store=True, copy=True)
    earnings_total = fields.Float( store=True, copy=True)
    deduction_total = fields.Float( store=True, copy=True)
    net_wage = fields.Float( store=True, copy=True)
    working_days = fields.Float( store=True, copy=True)
    basic_absent_days = fields.Float( store=True, copy=True)
    gross_absent_days = fields.Float( store=True, copy=True)
    friday_days = fields.Float( store=True, copy=True)
    holiday_days = fields.Float( store=True, copy=True)
    coff_days = fields.Float( store=True, copy=True)
    adjust_days = fields.Float( store=True, copy=True)
    od_days = fields.Float( store=True, copy=True)
    late_days = fields.Float( store=True, copy=True)
    cl_days = fields.Float( store=True, copy=True)
    sl_days = fields.Float( store=True, copy=True)
    el_days = fields.Float( store=True, copy=True)
    ml_days = fields.Float(store=True, copy=True)
    lw_days = fields.Float( store=True, copy=True)
    total_payable_days = fields.Float( store=True, copy=True)
    
    @api.depends('employee_id')
    def _compute_employee_contract(self):
        for payslip in self.filtered('employee_id'):
            payslip.job_id = payslip.employee_id.job_id
            payslip.department_id = payslip.employee_id.department_id
            
    def _get_salary_line_earnings_deduction_total(self, code):
        lines = self.line_ids.filtered(lambda line: line.category_id.code == code)
        return sum([line.total for line in lines])
    
    def _get_work_days_line_total(self, code):
        lines = self.worked_days_line_ids.filtered(lambda line: line.code == code)
        return sum([line.number_of_days for line in lines])    
    
    def _compute_basic_net(self):
        for payslip in self:
            
            if payslip.struct_id.name == 'FESTIVAL BONUS':
                payslip.gross_wage = payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL')
                payslip.basic_wage = payslip._get_salary_line_total('BASIC')
                payslip.hra_wage = payslip._get_salary_line_total('HRA')
                payslip.medical_wage = payslip._get_salary_line_total('MEDICAL')
                payslip.ot_wage = 0#payslip._get_salary_line_total('OT')
                payslip.arrear_wage = 0 #payslip._get_salary_line_total('ARREAR')
                payslip.att_bonus_wage = 0 #payslip._get_salary_line_total('ATTBONUS')
                payslip.convence_wage = 0#payslip._get_salary_line_total('CONVENCE')
                payslip.food_wage = 0#payslip._get_salary_line_total('FOOD')
                payslip.tiffin_wage = 0#payslip._get_salary_line_total('TIFFIN')
                payslip.snacks_wage = 0#payslip._get_salary_line_total('SNACKS')
                payslip.car_wage = 0#payslip._get_salary_line_total('CAR')
                payslip.others_alw_wage = payslip._get_salary_line_total('OTHERS_ALW')
                payslip.incentive_wage = 0#payslip._get_salary_line_total('INCENTIVE')
                payslip.rpf_wage = 0 #payslip._get_salary_line_total('RPF')
                payslip.earnings_total = payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('OTHERS_ALW')
                payslip.pf_empr_wage = 0 #payslip._get_salary_line_total('PFR')
                payslip.pf_empe_wage = 0 #payslip._get_salary_line_total('PFE')
                payslip.ait_wage = 0#payslip._get_salary_line_total('AIT')
                payslip.basic_absent_wage = 0#payslip._get_salary_line_total('BASIC_ABSENT')
                payslip.gross_absent_wage = 0#payslip._get_salary_line_total('GROSS_ABSENT')
                payslip.loan_wage = 0#payslip._get_salary_line_total('LOAN')
                payslip.adv_salary_wage = 0#payslip._get_salary_line_total('ADV_SALARY')
                payslip.others_ded_wage = 0#payslip._get_salary_line_total('OTHERS_DED')
                payslip.deduction_total = 0#payslip._get_salary_line_earnings_deduction_total('DED')
                payslip.net_wage = payslip._get_salary_line_total('NET')
                payslip.working_days = 0#payslip._get_work_days_line_total('P')
                payslip.basic_absent_days = 0#payslip._get_work_days_line_total('A')
                payslip.gross_absent_days = 0#payslip._get_work_days_line_total('X')
                payslip.friday_days = 0#payslip._get_work_days_line_total('F')
                payslip.holiday_days = 0#payslip._get_work_days_line_total('H')
                payslip.od_days = 0#payslip._get_work_days_line_total('OD')
                payslip.coff_days = 0#payslip._get_work_days_line_total('CO')
                payslip.adjust_days = 0#payslip._get_work_days_line_total('AJ')
                payslip.late_days = 0#payslip._get_work_days_line_total('L')
                payslip.cl_days = 0#payslip._get_work_days_line_total('CL')
                payslip.sl_days = 0#payslip._get_work_days_line_total('SL')
                payslip.el_days = 0#payslip._get_work_days_line_total('EL')
                payslip.ml_days = 0#payslip._get_work_days_line_total('ML')
                payslip.lw_days = 0#payslip._get_work_days_line_total('LW')
                payslip.total_payable_days = 0
            elif payslip.struct_id.name == 'F&F':
                payslip.gross_wage = payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL')
                payslip.basic_wage = payslip._get_salary_line_total('BASIC')
                payslip.hra_wage = payslip._get_salary_line_total('HRA')
                payslip.medical_wage = payslip._get_salary_line_total('MEDICAL')
                payslip.ot_wage = payslip._get_salary_line_total('OT')
                payslip.arrear_wage = payslip._get_salary_line_total('ARREAR')
                payslip.att_bonus_wage = payslip._get_salary_line_total('ATTBONUS')
                payslip.convence_wage = payslip._get_salary_line_total('CONVENCE')
                payslip.food_wage = payslip._get_salary_line_total('FOOD')
                payslip.tiffin_wage = payslip._get_salary_line_total('TIFFIN')
                payslip.snacks_wage = payslip._get_salary_line_total('SNACKS')
                payslip.car_wage = payslip._get_salary_line_total('CAR')
                payslip.others_alw_wage = (payslip._get_salary_line_total('OTHERS_ALW')+
                                          payslip._get_salary_line_total('EL')+
                                          payslip._get_salary_line_total('CB')+
                                          payslip._get_salary_line_total('EID')+
                                          payslip._get_salary_line_total('OB')+
                                          payslip._get_salary_line_total('PF'))
                payslip.incentive_wage = payslip._get_salary_line_total('INCENTIVE')
                payslip.rpf_wage = 0#payslip._get_salary_line_total('RPF')
                payslip.earnings_total = (payslip._get_salary_line_earnings_deduction_total('EARNINGS') +
                                          payslip._get_salary_line_earnings_deduction_total('BASIC') + 
                                          payslip._get_salary_line_earnings_deduction_total('HRA') + 
                                          payslip._get_salary_line_earnings_deduction_total('MEDICAL'))
                payslip.pf_empr_wage = 0#payslip._get_salary_line_total('PFR')
                payslip.pf_empe_wage = 0#payslip._get_salary_line_total('PFE')
                payslip.ait_wage = payslip._get_salary_line_total('AIT')
                payslip.basic_absent_wage = payslip._get_salary_line_total('BASIC_ABSENT')
                payslip.gross_absent_wage = payslip._get_salary_line_total('GROSS_ABSENT')
                payslip.loan_wage = payslip._get_salary_line_total('LOAN')
                payslip.adv_salary_wage = payslip._get_salary_line_total('ADV_SALARY')
                payslip.others_ded_wage = (payslip._get_salary_line_total('OTHERS_DED')+
                                          payslip._get_salary_line_total('NP')+
                                          payslip._get_salary_line_total('UO'))
                payslip.deduction_total = payslip._get_salary_line_earnings_deduction_total('DED')
                payslip.net_wage = payslip._get_salary_line_total('NET')
                payslip.working_days = payslip._get_work_days_line_total('P')
                payslip.basic_absent_days = payslip._get_work_days_line_total('A')
                payslip.gross_absent_days = payslip._get_work_days_line_total('X')
                payslip.friday_days = payslip._get_work_days_line_total('F')
                payslip.holiday_days = payslip._get_work_days_line_total('H')
                payslip.od_days = payslip._get_work_days_line_total('OD')
                payslip.coff_days = payslip._get_work_days_line_total('CO')
                payslip.adjust_days = payslip._get_work_days_line_total('AJ')
                payslip.late_days = payslip._get_work_days_line_total('L')
                payslip.cl_days = payslip._get_work_days_line_total('CL')
                payslip.sl_days = payslip._get_work_days_line_total('SL')
                payslip.el_days = payslip._get_work_days_line_total('EL')
                payslip.ml_days = payslip._get_work_days_line_total('ML')
                payslip.lw_days = payslip._get_work_days_line_total('LW')
                payslip.total_payable_days = (payslip._get_work_days_line_total('P') + payslip._get_work_days_line_total('F') +
                                              payslip._get_work_days_line_total('H') + payslip._get_work_days_line_total('AJ') + 
                                              payslip._get_work_days_line_total('CL') + payslip._get_work_days_line_total('OD') +
                                              payslip._get_work_days_line_total('SL') + payslip._get_work_days_line_total('EL'))
            else:
                payslip.gross_wage = payslip._get_salary_line_total('BASIC') + payslip._get_salary_line_total('HRA') + payslip._get_salary_line_total('MEDICAL')
                payslip.basic_wage = payslip._get_salary_line_total('BASIC')
                payslip.hra_wage = payslip._get_salary_line_total('HRA')
                payslip.medical_wage = payslip._get_salary_line_total('MEDICAL')
                payslip.ot_wage = payslip._get_salary_line_total('OT')
                payslip.arrear_wage = payslip._get_salary_line_total('ARREAR')
                payslip.att_bonus_wage = payslip._get_salary_line_total('ATTBONUS')
                payslip.convence_wage = payslip._get_salary_line_total('CONVENCE')
                payslip.food_wage = payslip._get_salary_line_total('FOOD')
                payslip.tiffin_wage = payslip._get_salary_line_total('TIFFIN')
                payslip.snacks_wage = payslip._get_salary_line_total('SNACKS')
                payslip.car_wage = payslip._get_salary_line_total('CAR')
                payslip.others_alw_wage = payslip._get_salary_line_total('OTHERS_ALW')
                payslip.incentive_wage = payslip._get_salary_line_total('INCENTIVE')
                payslip.rpf_wage = payslip._get_salary_line_total('RPF')
                payslip.earnings_total = (payslip._get_salary_line_earnings_deduction_total('EARNINGS') +
                                          payslip._get_salary_line_earnings_deduction_total('BASIC') + 
                                          payslip._get_salary_line_earnings_deduction_total('HRA') + 
                                          payslip._get_salary_line_earnings_deduction_total('MEDICAL'))
                payslip.pf_empr_wage = payslip._get_salary_line_total('PFR')
                payslip.pf_empe_wage = payslip._get_salary_line_total('PFE')
                payslip.ait_wage = payslip._get_salary_line_total('AIT')
                payslip.basic_absent_wage = payslip._get_salary_line_total('BASIC_ABSENT')
                payslip.gross_absent_wage = payslip._get_salary_line_total('GROSS_ABSENT')
                payslip.loan_wage = payslip._get_salary_line_total('LOAN')
                payslip.adv_salary_wage = payslip._get_salary_line_total('ADV_SALARY')
                payslip.others_ded_wage = payslip._get_salary_line_total('OTHERS_DED')
                payslip.deduction_total = payslip._get_salary_line_earnings_deduction_total('DED')
                payslip.net_wage = payslip._get_salary_line_total('NET')
                payslip.working_days = payslip._get_work_days_line_total('P')
                payslip.basic_absent_days = payslip._get_work_days_line_total('A')
                payslip.gross_absent_days = payslip._get_work_days_line_total('X')
                payslip.friday_days = payslip._get_work_days_line_total('F')
                payslip.holiday_days = payslip._get_work_days_line_total('H')
                payslip.od_days = payslip._get_work_days_line_total('OD')
                payslip.coff_days = payslip._get_work_days_line_total('CO')
                payslip.adjust_days = payslip._get_work_days_line_total('AJ')
                payslip.late_days = payslip._get_work_days_line_total('L')
                payslip.cl_days = payslip._get_work_days_line_total('CL')
                payslip.sl_days = payslip._get_work_days_line_total('SL')
                payslip.el_days = payslip._get_work_days_line_total('EL')
                payslip.ml_days = payslip._get_work_days_line_total('ML')
                payslip.lw_days = payslip._get_work_days_line_total('LW')
                payslip.total_payable_days = (payslip._get_work_days_line_total('P') + payslip._get_work_days_line_total('F') +
                                              payslip._get_work_days_line_total('H') + payslip._get_work_days_line_total('AJ') + 
                                              payslip._get_work_days_line_total('CL') + payslip._get_work_days_line_total('OD') +
                                              payslip._get_work_days_line_total('SL') + payslip._get_work_days_line_total('EL'))                
                
            
    @api.depends('contract_id','date_from','date_to')
    def _compute_ot_rate(self):
        for payslip in self:
            emp_list = self.env['hr.employee'].search([('id', '=', payslip.employee_id.id)])#,("active", '=', True)
            att_record = self.env['hr.attendance'].search([('employee_id', '=', payslip.employee_id.id),('attDate', '>=',payslip.date_from),('attDate', '<=',payslip.date_to)])
            if emp_list.isovertime is True:
                payslip.otRate = round(((payslip.contract_id.basic/208)*2),2)
                payslip.otHours = sum(att_record.mapped('otHours'))
                payslip.com_otHours = sum(att_record.mapped('com_otHours'))
            else:
                payslip.otRate = 0.0
                payslip.otHours = 0.0
                payslip.com_otHours = 0.0
                
    @api.onchange('employee_id', 'struct_id', 'contract_id', 'date_from', 'date_to')
    def _onchange_employee(self):
        if (not self.employee_id) or (not self.date_from) or (not self.date_to):
            return

        employee = self.employee_id
        date_from = self.date_from
        date_to = self.date_to

        self.company_id = employee.company_id
        if not self.contract_id or self.employee_id != self.contract_id.employee_id: # Add a default contract if not already defined
            contracts = employee._get_contracts(date_from, date_to)

            if not contracts or not contracts[0].structure_type_id.default_struct_id:
                self.contract_id = False
                self.struct_id = False
                return
            self.contract_id = contracts[0]
            self.struct_id = contracts[0].structure_type_id.default_struct_id

        lang = employee.sudo().address_home_id.lang or self.env.user.lang
        context = {'lang': lang}
        
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        if payslip_run.is_bonus:
            payslip_name = self.struct_id.payslip_name or _('Festival Bonus Slip')
        elif payslip_run.is_final:
            payslip_name = self.struct_id.payslip_name or _('Full & Final Slip')
        else:
            payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        del context

        self.name = '%s - %s - %s' % (
            payslip_name,
            self.employee_id.name or '',
            format_date(self.env, self.date_to, date_format="MMMM y", lang_code=lang)
        )

#         if date_to > date_utils.end_of(fields.Date.today(), 'month'):
#             self.warning_message = _(
#                 "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
#                 start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
#                 end=date_to,
#             )
#         else:
#             self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()
              
    
    def action_payslip_done(self):
        if any(slip.state == 'cancel' for slip in self):
            raise ValidationError(_("You can't validate a cancelled payslip."))
        self.write({'state' : 'done'})
        self.mapped('payslip_run_id').action_close()
        # Validate attendance_entries for regular payslips (exclude end of year bonus, ...)
        if self.mapped('payslip_run_id').is_bonus == False:
            regular_payslips = self.filtered(lambda p: p.struct_id.type_id.default_struct_id == p.struct_id)
            for regular_payslip in regular_payslips:
                attendance_entries = self.env['hr.attendance'].search([
                    ('attDate', '<=', regular_payslip.date_to),
                    ('attDate', '>=', regular_payslip.date_from),
                    ('employee_id', '=', regular_payslip.employee_id.id),
                ])
                attendance_entries.write({'is_lock' : True})
                
                
                emp = self.env['hr.employee'].search([('id', '=', regular_payslip.employee_id.id),])
                # for rec in emp:
                pf_total = emp.contribution_sum
                pf_total += regular_payslip.pf_empe_wage
                # odoo_pf = abs(sum(emp.providient_pay_line_ids.mapped('total')))
                # tms_pf_record = self.env['provident.fund.line'].search([('employee_id', '=', emp.id)])
                # tms_pf = 0
                # if tms_pf_record:
                #     tms_pf = abs(sum(tms_pf_record.mapped('pf_amount')))
                emp.update({'contribution_sum' : pf_total})     

        query_ = """truncate table hr_work_entry;"""
        self.env.cr.execute(query_)
        
        generate = self.env.context.get('payslip_generate_pdf', True)
        if self.env.context.get('payslip_generate_pdf') or generate is True:
            # raise UserError(('dd'))
            for payslip in self:
                if not payslip.struct_id or not payslip.struct_id.report_id:
                    report = self.env.ref('hr_payroll.action_report_payslip', False)
                else:
                    report = payslip.struct_id.report_id
                pdf_content, content_type = report.sudo()._render_qweb_pdf(payslip.id)
                if payslip.struct_id.report_id.print_report_name:
                    pdf_name = safe_eval(payslip.struct_id.report_id.print_report_name, {'object': payslip})
                else:
                    if self.mapped('payslip_run_id').is_bonus:
                        pdf_name = _('Festival Bonus Slip')
                    elif self.mapped('payslip_run_id').is_final:
                        pdf_name = _('Full & Final Slip')
                    else:
                        pdf_name = _("Payslip")
                # Sudo to allow payroll managers to create document.document without access to the
                # application
                attachment = self.env['ir.attachment'].sudo().create({
                    'name': pdf_name,
                    'type': 'binary',
                    'datas': base64.encodebytes(pdf_content),
                    'res_model': payslip._name,
                    'res_id': payslip.id
                })
                # Send email to employees
                subject = '%s, a new payslip is available for you' % (payslip.employee_id.name)
                template = self.env.ref('hr_payroll.mail_template_new_payslip', raise_if_not_found=False)
                if template:
                    email_values = {
                        'attachment_ids': attachment,
                    }
                    template.send_mail(
                        payslip.id,
                        email_values=email_values,
                        notif_layout='mail.mail_notification_light')    
    
    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        att_obj = self.env['hr.attendance']
        leave_obj = self.env['hr.leave']

        basic_absent_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', ('A'))])
        ba_days = len(basic_absent_record)
        ba_hours = sum(basic_absent_record.mapped('worked_hours'))
        
        gross_absent_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', ('X'))])
        ga_days = len(gross_absent_record)
        ga_hours = sum(gross_absent_record.mapped('worked_hours'))

        friday_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'F')])
        f_days = len(friday_record)
        f_hours = sum(friday_record.mapped('worked_hours')) 
        
        holiday_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'H')])
        h_days = len(holiday_record)
        h_hours = sum(holiday_record.mapped('worked_hours'))        
        
#         friday_precord = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'FP')])
#         fp_days = len(friday_precord)
#         fp_hours = sum(friday_precord.mapped('worked_hours')) 
        
#         holiday_precord = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'HP')])
#         hp_days = len(holiday_precord)
#         hp_hours = sum(holiday_precord.mapped('worked_hours'))                
        
        present_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', 'in', ('P','L','HP','FP','CO'))])
        p_days = len(present_record)
        p_hours = sum(present_record.mapped('worked_hours'))
                
        late_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'L')])
        l_days = len(late_record)
        l_hours = sum(late_record.mapped('worked_hours'))
        
        early_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('outFlag', '=', 'EO')])
        e_days = len(early_record)
        e_hours = sum(early_record.mapped('worked_hours'))
        
        co_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'CO')])
        c_days = len(co_record)
        c_hours = sum(co_record.mapped('worked_hours'))
        
        aj_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'AJ')])
        a_days = len(aj_record)
        a_hours = sum(aj_record.mapped('worked_hours'))
        
        tiffin_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('otHours', '>=', 2.0),('inFlag', 'not in', ('HP','FP'))])
        t_days = len(tiffin_record)
        t_hours = sum(tiffin_record.mapped('worked_hours'))

    
        cl_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'CL')])
        cl_days = len(cl_record)
        cl_hours = False
        
        sl_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'SL')])
        sl_days = len(sl_record)
        sl_hours = False
        
        el_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'EL')])
        el_days = len(el_record)
        el_hours = False
        
        # ml_record = leave_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('date_from', '>=',self.date_from),('date_to', '<=',self.date_to),('holiday_status_id.code', '=', 'ML')])
        # ml_days = sum(ml_record.mapped('number_of_days'))
        # ml_hours = False
        
        ml_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'ML')])
        ml_days = len(ml_record)
        ml_hours = False
        
        lw_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'LW')])
        lw_days = len(lw_record)
        lw_hours = False
        
        od_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'OD')])
        o_days = len(od_record)
        o_hours = False          
        
        #raise UserError((cl_days))
                
        if cl_days>0:#'CL'
            day_rounded=cl_days
            hours=cl_hours
            attendance_line = {
                'sequence': 2,
                'work_entry_type_id': 106,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if sl_days>0:#'SL'
            day_rounded=sl_days
            hours=sl_hours
            attendance_line = {
                'sequence': 3,
                'work_entry_type_id': 109,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if el_days>0:#'EL'
            day_rounded=el_days
            hours=el_hours
            attendance_line = {
                'sequence': 4,
                'work_entry_type_id': 110,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if ml_days>0:#'ML'
            day_rounded=ml_days
            hours=ml_hours
            attendance_line = {
                'sequence': 5,
                'work_entry_type_id': 111,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if lw_days>0:#'LW'
            day_rounded=lw_days
            hours=lw_hours
            attendance_line = {
                'sequence': 6,
                'work_entry_type_id': 108,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)            
        if ba_days>0:#'A'
            day_rounded=ba_days
            hours=ba_hours
            attendance_line = {
                'sequence': 13,
                'work_entry_type_id': 115,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if ga_days>0:#'X'
            day_rounded=ga_days
            hours=ga_hours
            attendance_line = {
                'sequence': 12,
                'work_entry_type_id': 117,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)            
        if f_days>0:#'F'
            day_rounded=f_days
            hours=f_hours
            attendance_line = {
                'sequence': 11,
                'work_entry_type_id': 114,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)            
        if h_days>0:#'H'
            day_rounded=h_days
            hours=h_hours
            attendance_line = {
                'sequence': 10,
                'work_entry_type_id': 113,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)            
        if p_days>0:#'P'
            day_rounded=p_days
            hours=p_hours
            attendance_line = {
                'sequence': 1,
                'work_entry_type_id': 1,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if l_days>0:#L
            day_rounded=l_days
            hours=l_hours
            attendance_line = {
                'sequence': 14,
                'work_entry_type_id': 118,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if e_days>0:#EO
            day_rounded=e_days
            hours=e_hours
            attendance_line = {
                'sequence': 17,
                'work_entry_type_id': 121,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if c_days>0:#CO
            day_rounded=c_days
            hours=c_hours
            attendance_line = {
                'sequence': 8,
                'work_entry_type_id': 119,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if a_days>0:#AJ
            day_rounded=a_days
            hours=a_hours
            attendance_line = {
                'sequence': 7,
                'work_entry_type_id': 107,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if o_days>0:#OD
            day_rounded=o_days
            hours=o_hours
            attendance_line = {
                'sequence': 9,
                'work_entry_type_id': 112,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        if t_days>0:#T
            day_rounded=t_days
            hours=t_hours
            attendance_line = {
                'sequence': 15,
                'work_entry_type_id': 116,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        return res
    def _get_worked_day_lines(self, domain=None, check_out_of_contract=True):
        """
        :returns: a list of dict containing the worked days values that should be applied for the given payslip
        """
        res = []
        # fill only if the contract as a working schedule linked
        self.ensure_one()
        contract = self.contract_id
        if contract.resource_calendar_id:
            res = self._get_worked_day_lines_values(domain=domain)
            # """if not check_out_of_contract:
            #     return res

            # # If the contract doesn't cover the whole month, create
            # # worked_days lines to adapt the wage accordingly
            # out_days, out_hours = 0, 0
            # reference_calendar = self._get_out_of_contract_calendar()
            # if self.date_from < contract.date_start:
            #     start = fields.Datetime.to_datetime(self.date_from)
            #     stop = fields.Datetime.to_datetime(contract.date_start) + relativedelta(days=-1, hour=23, minute=59)
            #     out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False)
            #     out_days += out_time['days']
            #     out_hours += out_time['hours']
            # if contract.date_end and contract.date_end < self.date_to:
            #     start = fields.Datetime.to_datetime(contract.date_end) + relativedelta(days=1)
            #     stop = fields.Datetime.to_datetime(self.date_to) + relativedelta(hour=23, minute=59)
            #     out_time = reference_calendar.get_work_duration_data(start, stop, compute_leaves=False)
            #     out_days += out_time['days']
            #     out_hours += out_time['hours']

            # if out_days or out_hours:
            #     work_entry_type = self.env.ref('hr_payroll.hr_work_entry_type_out_of_contract')
            #     res.append({
            #         'sequence': work_entry_type.sequence,
            #         'work_entry_type_id': work_entry_type.id,
            #         'number_of_days': out_days,
            #         'number_of_hours': out_hours,
            #     })"""
        return res    
    
    def _input_compute_sheet(self, payslip_id, contract_id, employee_id, date_start, date_stop):
        others_adjust = self.env['hr.payslip.input']
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        
        if payslip_run.is_bonus:
            input = self.env['salary.adjustment'].search([('salary_month', '=', date_stop), ('salary_month', '=', date_start), ('adjust_type', '=', 'bonus')])
        elif payslip_run.is_final:
            input = self.env['salary.adjustment'].search([('salary_month', '<=', date_stop), ('salary_month', '>=', date_start), ('adjust_type', '=', 'fnf')])
        else:
            input = self.env['salary.adjustment'].search([('salary_month', '<=', date_stop), ('salary_month', '>=', date_start), ('adjust_type', '=', 'sal')])
        for line in input:
            input_entries = self.env['salary.adjustment.line'].search([('adjustment_id', '=', line.id),
                                                                       ('employee_id', '=', int(employee_id))])
            
            if input_entries:
                for type in input_entries:
                    adjust_exist = self.env['hr.payslip.input'].search([('payslip_id', '=', payslip_id), ('input_type_id', '=', int(type.adjustment_type))])
                    if adjust_exist:
                        amount = sum(adjust_exist.mapped('amount'))
                        amount = amount + sum(type.mapped('amount'))
                        adjust_exist.write({'amount': amount})
                    else:
                        others_adjust.create({'payslip_id': payslip_id,
                                              'sequence':10,
                                              'input_type_id': int(type.adjustment_type),
                                              'contract_id':contract_id,
                                              'amount': sum(type.mapped('amount'))})
                
    def action_refresh_from_work_entries(self):
        # Refresh the whole payslip in case the HR has modified some work entries
        # after the payslip generation
        self.ensure_one()
        self._onchange_employee()
        self.compute_sheet()
        
    def compute_sheet(self):
        # Refresh the whole payslip in case the HR has entry some adjustment entries
        # after the payslip generation
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        # delete old payslip lines 
        payslips.line_ids.unlink()
        #payslips.input_line_ids.unlink()
        for payslip in payslips:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
            payslip.input_line_ids.unlink()
            payslip._input_compute_sheet(payslip.id, payslip.contract_id, payslip.employee_id, payslip.date_from, payslip.date_to)
            payslip._compute_basic_net()
        return True

class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'
    _description = 'Payslip Input Type'
    
    is_deduction = fields.Boolean(string="is Deduct", store=True)
    
    

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'
    _description = 'Payslip Batches'
    _order = 'date_end desc'

    is_bonus = fields.Boolean(string='Festival Bonus', readonly=True,
        states={'draft': [('readonly', False)]},
        help="If its checked, indicates that all payslips generated from here are Festival Bonus payslips.")
    
    is_final = fields.Boolean(string='Full & Final', readonly=True,
        states={'draft': [('readonly', False)]},
        help="If its checked, indicates that all payslips generated from here are Full & Final payslips.")

    def _compute_payslip_count(self):
        for payslip_run in self:
            payslip_run.payslip_count = len(payslip_run.slip_ids)

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_close(self):
        if self._are_payslips_ready():
            if self.is_final:
                query = """update hr_employee set active=False where resign_date<=%s and resign_date>=%s and company_id=%s;"""
                self.env.cr.execute(query,(self.date_end,self.date_start,self.company_id.id))
                # result = self.env.cr.fetchall()
                # Update employees' active status to False
                # self.mapped('slip_ids.employee_id').write({'active': False})
            self.write({'state' : 'close'})

    def action_validate(self):
        self.mapped('slip_ids').filtered(lambda slip: slip.state != 'cancel').action_payslip_done()    
        self.action_close()

    def action_open_payslips(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "res_model": "hr.payslip",
            "views": [[False, "tree"], [False, "form"]],
            "domain": [['id', 'in', self.slip_ids.ids]],
            "name": "Payslips",
        }

    def unlink(self):
        if any(self.filtered(lambda payslip_run: payslip_run.state not in ('draft'))):
            raise UserError(_('You cannot delete a payslip batch which is not draft!'))
        if any(self.mapped('slip_ids').filtered(lambda payslip: payslip.state not in ('draft','cancel'))):
            raise UserError(_('You cannot delete a payslip which is not draft or cancelled!'))
        return super(HrPayslipRun, self).unlink()

    def _are_payslips_ready(self):
        return all(slip.state in ['done', 'cancel'] for slip in self.mapped('slip_ids'))
