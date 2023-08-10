# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime, date, time, timedelta
from dateutil.relativedelta import relativedelta
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployee(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'
    
    def _get_available_contracts_domain(self):
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        from_date = payslip_run.date_start
        # raise UserError((from_date))
        from_date = from_date + relativedelta(months=-6)
        start_date = payslip_run.date_start
        end_date = payslip_run.date_end
        # raise UserError((from_date))
        if payslip_run.is_bonus:
            return [('category_ids', 'not like', ('Expatriate')),('contract_ids.state', 'in', ('open', 'close')), ('contract_ids.date_start', '<=', from_date), ('company_id', '=', self.env.company.id)]
        elif payslip_run.is_final:
            return [('resign_date', '<=', end_date),('resign_date', '>=', start_date),('company_id', '=', self.env.company.id)]
        else:
            return [('contract_ids.state', 'in', ('open', 'close')), ('company_id', '=', self.env.company.id)]

    def _get_employees(self):
        active_employee_ids = self.env.context.get('active_employee_ids', False)
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        if active_employee_ids:
            return self.env['hr.employee'].browse(active_employee_ids)
               # YTI check dates too
        if payslip_run.is_final:
            query = """
            update hr_contract set active=True where active=False and date_end<=%s and date_end>=%s and company_id=%s;
            update hr_employee set active=True where active=False and resign_date<=%s and resign_date>=%s and company_id=%s;"""
            self.env.cr.execute(query,(payslip_run.date_end,payslip_run.date_start,payslip_run.company_id.id,payslip_run.date_end,payslip_run.date_start,payslip_run.company_id.id))
            # contract_id
            # result = self.env.cr.fetchall()
            # emp = self.env['hr.employee'].search([('id', '=', result), ('active', '=', False)])
            # if emp:
            #     emp.active = True
        return self.env['hr.employee'].search(self._get_available_contracts_domain())
        
    def _get_structure(self):
        payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))
        if payslip_run.is_final:
            structure = self.env['hr.payroll.structure'].search([('name', '=', 'F&F')])
        elif payslip_run.is_bonus:
            structure = self.env['hr.payroll.structure'].search([('name', '=', 'FESTIVAL BONUS')])
        else:
            structure = self.env['hr.payroll.structure']

        return structure   

    employee_ids = fields.Many2many('hr.employee', 'hr_employee_group_rel', 'payslip_id', 'employee_id', 'Employees', default=lambda self: self._get_employees(), required=True)
    structure_id = fields.Many2one('hr.payroll.structure', default=lambda self: self._get_structure(), string='Salary Structure')    


    def _check_undefined_slots(self, work_entries, payslip_run):
        """
        Check if a time slot in the contract's calendar is not covered by a work entry
        """
        work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])
        for work_entry in work_entries:
            work_entries_by_contract[work_entry.contract_id] |= work_entry

        for contract, work_entries in work_entries_by_contract.items():
            calendar_start = pytz.utc.localize(datetime.combine(max(contract.date_start, payslip_run.date_start), time.min))
            calendar_end = pytz.utc.localize(datetime.combine(min(contract.date_end or date.max, payslip_run.date_end), time.max))
            outside = contract.resource_calendar_id._attendance_intervals_batch(calendar_start, calendar_end)[False] - work_entries._to_intervals()

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
                        #input_entries.amount            
    def compute_sheet(self):
        self.ensure_one()
        if not self.env.context.get('active_id'):
            from_date = fields.Date.to_date(self.env.context.get('default_date_start'))
            end_date = fields.Date.to_date(self.env.context.get('default_date_end'))
            payslip_run = self.env['hr.payslip.run'].create({
                'name': from_date.strftime('%B %Y'),
                'date_start': from_date,
                'date_end': end_date,
            })
        else:
            payslip_run = self.env['hr.payslip.run'].browse(self.env.context.get('active_id'))

        employees = self.with_context(active_test=False).employee_ids
        
        # raise UserError((employees))
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']
        
        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)

        default_values = Payslip.default_get(Payslip.fields_get())
        if payslip_run.is_final:
            payslip_values = [dict(default_values, **{
                'name': 'Fnfslip - %s' % (contract.employee_id.name),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': contract.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            }) for contract in contracts]
        elif payslip_run.is_bonus:
            payslip_values = [dict(default_values, **{
                'name': 'Festivalslip - %s' % (contract.employee_id.name),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            }) for contract in contracts]
        else:
            payslip_values = [dict(default_values, **{
                'name': 'Payslip - %s' % (contract.employee_id.name),
                'employee_id': contract.employee_id.id,
                'credit_note': payslip_run.credit_note,
                'payslip_run_id': payslip_run.id,
                'date_from': payslip_run.date_start,
                'date_to': payslip_run.date_end,
                'contract_id': contract.id,
                'struct_id': self.structure_id.id or contract.structure_type_id.default_struct_id.id,
            }) for contract in contracts]

        payslips = Payslip.with_context(tracking_disable=True).create(payslip_values)
        for payslip in payslips:
            payslip._onchange_employee()
            payslip._input_compute_sheet(payslip.id, payslip.contract_id, payslip.employee_id, payslip.date_from, payslip.date_to)

        payslips.compute_sheet()
        payslip_run.state = 'verify'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'hr.payslip.run',
            'views': [[False, 'form']],
            'res_id': payslip_run.id,
        }
                

 