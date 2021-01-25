# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import pytz
from itertools import chain
from odoo import models

from odoo.addons.hr_work_entry_contract.models.hr_work_intervals import WorkIntervals


class HrContract(models.Model):
    _inherit = 'hr.contract'
    _description = "Contract"

    # def _get_contract_work_entries_values(self, date_start, date_stop):
    #     values = super()._get_contract_work_entries_values(date_start, date_stop)

    #     overtimes = self.env['hr.overtime'].sudo().search([
    #         ('employee_id', '=', self.employee_id.id),
    #         ('start_date', '<=', date_stop),
    #         ('end_date', '>=', date_start),
    #     ])
    #     # Create a work entry only if the overtime is not inside a leave
    #     leave_intervals = self.resource_calendar_id._leave_intervals(
    #         start_dt=pytz.utc.localize(date_start),
    #         end_dt=pytz.utc.localize(date_stop),
    #         resource=self.employee_id.resource_id,
    #     )
    #     overtime_intervals = WorkIntervals([
    #         (
    #             pytz.utc.localize(max(overtime.start_date, date_start)),
    #             pytz.utc.localize(min(overtime.end_date, date_stop)),
    #             overtime,
    #         ) for overtime in overtimes
    #     ])
    #     overtime_ids = chain.from_iterable(records.ids for start, end, records in overtime_intervals - leave_intervals)
    #     overtimes = self.env['hr.overtime'].browse(set(overtime_ids))
    #     return values + [
    #         dict(
    #             overtime._get_work_entry_values(self),
    #             date_start=max(overtime.start_date, date_start),
    #             date_stop=min(overtime.end_date, date_stop),
    #         )
    #         for overtime in overtimes
    #     ]
