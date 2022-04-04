# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from collections import defaultdict
from datetime import datetime, date, time
import pytz

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrPayslipEmployee(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

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
            #raise UserError((calendar_start, calendar_end, outside))
            #if outside:
                #raise UserError(_("Some part of %s's calendar is not covered by any work entry. Please complete the schedule.", contract.employee_id.name))
#     def _input_compute_sheet(self, payslip_id, contract_id, employee_id, date_start, date_stop):
#         others_adjust = self.env['hr.payslip.input']
#         input = self.env['salary.adjustment'].search([('salary_month', '<=', date_stop), ('salary_month', '>=', date_start)])
#         for line in input:
#             input_entries = self.env['salary.adjustment.line'].search([('adjustment_id', '=', line.id),
#                                                                        ('employee_id', '=', int(employee_id))])
#             if input_entries:
#                 others_adjust.create({'payslip_id': payslip_id,
#                                       'sequence':10,
#                                       'input_type_id': int(input_entries.adjustment_type),
#                                       'contract_id':contract_id,
#                                       'amount': sum(input_entries.mapped('amount'))})#input_entries.amount
    def _input_compute_sheet(self, payslip_id, contract_id, employee_id, date_start, date_stop):
        others_adjust = self.env['hr.payslip.input']
        input = self.env['salary.adjustment'].search([('salary_month', '<=', date_stop), ('salary_month', '>=', date_start)])
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
        if not employees:
            raise UserError(_("You must select employee(s) to generate payslip(s)."))

        payslips = self.env['hr.payslip']
        Payslip = self.env['hr.payslip']
        
        contracts = employees._get_contracts(
            payslip_run.date_start, payslip_run.date_end, states=['open', 'close']
        ).filtered(lambda c: c.active)
        contracts._generate_work_entries(payslip_run.date_start, payslip_run.date_end)
        work_entries = self.env['hr.work.entry'].search([
            ('date_start', '<=', payslip_run.date_end),
            ('date_stop', '>=', payslip_run.date_start),
            ('employee_id', 'in', employees.ids),
        ])
        self._check_undefined_slots(work_entries, payslip_run)

        if(self.structure_id.type_id.default_struct_id == self.structure_id):
            work_entries = work_entries.filtered(lambda work_entry: work_entry.state != 'validated')
            if work_entries._check_if_error():
                work_entries_by_contract = defaultdict(lambda: self.env['hr.work.entry'])

                for work_entry in work_entries.filtered(lambda w: w.state == 'conflict'):
                    work_entries_by_contract[work_entry.contract_id] |= work_entry

                for contract, work_entries in work_entries_by_contract.items():
                    conflicts = work_entries._to_intervals()
                    time_intervals_str = "\n - ".join(['', *["%s -> %s" % (s[0], s[1]) for s in conflicts._items]])
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Some work entries could not be validated.'),
                        'message': _('Time intervals to look for:%s', time_intervals_str),
                        'sticky': False,
                    }
                }


        default_values = Payslip.default_get(Payslip.fields_get())
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
                

 