# -*- coding:utf-8 -*-
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
import math
import pytz

class HrPayslipsss(models.Model):
    _inherit = 'hr.payslip'
    _description = 'Pay Slip'
    
    otHours = fields.Float(compute="_compute_ot_rate", string = "OT Hours", store=True, copy=True)
    otRate = fields.Float(compute="_compute_ot_rate", string = "OT Rate", store=True, copy=True)
  
    @api.depends('contract_id','date_from','date_to')
    def _compute_ot_rate(self):
        for payslip in self:
            emp_list = self.env['hr.employee'].search([('id', '=', payslip.employee_id.id),("active", '=', True)])
            att_record = self.env['hr.attendance'].search([('employee_id', '=', payslip.employee_id.id),('attDate', '>=',payslip.date_from),('attDate', '<=',payslip.date_to)])
            if emp_list.isOverTime is True:
                #raise UserError((self.contract_id.wage))
                #payslip.otRate = round((((payslip._get_salary_line_total('BASIC'))/208)*2),2)
                payslip.otRate = round(((self.contract_id.basic/208)*2),2)
                payslip.otHours = sum(att_record.mapped('otHours'))
            else:
                payslip.otRate = 0.0
                payslip.otHours = 0.0
                
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
        payslip_name = self.struct_id.payslip_name or _('Salary Slip')
        del context

        self.name = '%s - %s - %s' % (
            payslip_name,
            self.employee_id.name or '',
            format_date(self.env, self.date_to, date_format="MMMM y", lang_code=lang)
        )

        if date_to > date_utils.end_of(fields.Date.today(), 'month'):
            self.warning_message = _(
                "This payslip can be erroneous! Work entries may not be generated for the period from %(start)s to %(end)s.",
                start=date_utils.add(date_utils.end_of(fields.Date.today(), 'month'), days=1),
                end=date_to,
            )
        else:
            self.warning_message = False

        self.worked_days_line_ids = self._get_new_worked_days_lines()                
    
    def _get_worked_day_lines_values(self, domain=None):
        self.ensure_one()
        res = []
        att_obj = self.env['hr.attendance']

        
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
        
        od_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'OD')])
        o_days = len(od_record)
        o_hours = sum(od_record.mapped('worked_hours'))        
        
        tiffin_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('otHours', '>=', 2.0),('inFlag', 'not in', ('HP','FP'))])
        t_days = len(tiffin_record)
        t_hours = sum(tiffin_record.mapped('worked_hours'))
        
        cl_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'CL')])
        cl_days = len(cl_record)
        cl_hours = sum(cl_record.mapped('worked_hours'))
        
        sl_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'SL')])
        sl_days = len(sl_record)
        sl_hours = sum(sl_record.mapped('worked_hours'))
        
        el_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'EL')])
        el_days = len(el_record)
        el_hours = sum(el_record.mapped('worked_hours'))
        
        ml_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'ML')])
        ml_days = len(ml_record)
        ml_hours = sum(ml_record.mapped('worked_hours'))
        
        lw_record = att_obj.search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', '=', 'LW')])
        lw_days = len(lw_record)
        lw_hours = sum(lw_record.mapped('worked_hours'))        
                
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
    
    
    def _input_compute_sheet(self, payslip_id, contract_id, employee_id, date_start, date_stop):
        others_adjust = self.env['hr.payslip.input']
        input = self.env['salary.adjustment'].search([('salary_month', '<=', date_stop), ('salary_month', '>=', date_start)])
        for line in input:
            input_entries = self.env['salary.adjustment.line'].search([('adjustment_id', '=', line.id),
                                                                       ('employee_id', '=', int(employee_id))])
            if input_entries:
                others_adjust.create({'payslip_id': payslip_id,'sequence':10,'input_type_id': int(input_entries.adjustment_type),
                                      'contract_id':contract_id,
                                      'amount': input_entries.amount})
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
            payslips.input_line_ids.unlink()
            self._input_compute_sheet(payslip.id, payslip.contract_id, payslip.employee_id, payslip.date_from, payslip.date_to)
        return True

class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'
    _description = 'Payslip Input Type'
    
    is_deduction = fields.Boolean(string="is Deduct", store=True)
