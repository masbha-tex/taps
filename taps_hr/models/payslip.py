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
                #raise UserError((contract_id.wage))
                #payslip.otRate = round((((payslip._get_salary_line_total('BASIC'))/208)*2),2)
                payslip.otRate = round((((payslip._get_contract_wage()*0.60)/208)*2),2)
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
        att_record = self.env['hr.attendance'].search([('employee_id', '=', int(self.contract_id.employee_id)),('attDate', '>=',self.date_from),('attDate', '<=',self.date_to),('inFlag', 'in', ('P','L','HP','FP','CO'))])
        valdays = len(att_record)
        valhours = sum(att_record.mapped('worked_hours'))
        hours_per_day = self._get_worked_day_lines_hours_per_day()
        work_hours = self.contract_id._get_work_hours(self.date_from, self.date_to, domain=domain)
        work_hours_ordered = sorted(work_hours.items(), key=lambda x: x[1])
        biggest_work = work_hours_ordered[-1][0] if work_hours_ordered else 0
        add_days_rounding = 0
        for work_entry_type_id, hours in work_hours_ordered:
            work_entry_type = self.env['hr.work.entry.type'].browse(work_entry_type_id)
            days = round(hours / hours_per_day, 5) if hours_per_day else 0
            if work_entry_type_id == biggest_work:
                days += add_days_rounding
            day_rounded = self._round_days(work_entry_type, days)
            add_days_rounding += (days - day_rounded)
            if (work_entry_type_id==1):
                day_rounded=valdays
                hours=valhours
            attendance_line = {
                'sequence': work_entry_type.sequence,
                'work_entry_type_id': work_entry_type_id,
                'number_of_days': day_rounded,
                'number_of_hours': hours,
            }
            res.append(attendance_line)
        return res
    
    
    def action_refresh_from_work_entries(self):
        # Refresh the whole payslip in case the HR has modified some work entries
        # after the payslip generation
        self.ensure_one()
        self._onchange_employee()
        self.compute_sheet()
        #self.re_compute_sheet()
        
    def re_compute_sheet(self):
        # Refresh the whole payslip in case the HR has entry some adjustment entries
        # after the payslip generation
        payslips = self.filtered(lambda slip: slip.state in ['draft', 'verify'])
        # delete old payslip lines 
        raise UserError((payslips))
        payslips.line_ids.unlink()
        payslips.input_line_ids.unlink()
        for payslip in payslips:
            number = payslip.number or self.env['ir.sequence'].next_by_code('salary.slip')
            lines = [(0, 0, line) for line in payslip._get_payslip_lines()]
            payslip.write({'line_ids': lines, 'number': number, 'state': 'verify', 'compute_date': fields.Date.today()})
        return True

class HrPayslipInputType(models.Model):
    _inherit = 'hr.payslip.input.type'
    _description = 'Payslip Input Type'
    
    is_deduction = fields.Boolean(string="is Deduct", store=True)
    
    
class HrPayslipInput(models.Model):
    _inherit = 'hr.payslip.input'
    _description = 'Payslip Input'
    _order = 'payslip_id, sequence'


