# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.osv import expression


class HrOvertime(models.Model):
    _name = 'hr.overtime'
    _description = "Overitime"

    name = fields.Char(compute='_compute_name', store=True)
    employee_id = fields.Many2one('hr.employee', string="Employee")
    start_date = fields.Datetime("Start Time")
    end_date = fields.Datetime("End Time")
    number_of_hours = fields.Float("Number Of Hours", compute='_compute_number_of_hours')

    warning_extra_overtime = fields.Boolean("Has Extra Overtime", compute='_compute_warning_extra_overtime')
    extra_overtime_behaviour = fields.Selection([('warning', 'Warning'), ('ignore', 'Ignore'), ('include', 'Include')], default='warning', string="Extra Overtime Behaviour")

    work_entry_ids = fields.One2many('hr.work.entry', 'overtime_id')
    pending_work_entry_ids = fields.One2many('hr.work.entry', 'overtime_id',
        help="Work entries linked to the overtime which have not been validated yet.",
        domain=[('state', 'not in', ('validated', 'cancelled'))],
        groups="hr.group_hr_user")

    _sql_constraints = [
        ('_overtime_has_end', 'check (end_date IS NOT NULL)', 'Overtime must end. Please define an end date or a duration.'),
        ('_overtime_start_before_end', 'check (end_date > start_date)', 'Starting time should be before end time.')
    ]

    @api.depends('employee_id', 'start_date')
    def _compute_name(self):
        for record in self:
            if record.employee_id and record.start_date:
                record.name = "%s: %s" % (record.employee_id.name, fields.Date.to_string(record.start_date.date()))

    def _compute_warning_extra_overtime(self):
        for overtime in self:
            if overtime.work_entry_ids and overtime.extra_overtime_behaviour == 'warning':
                start = min(overtime.work_entry_ids.mapped('date_start'))
                end = max(overtime.work_entry_ids.mapped('date_stop'))
                overtime.warning_extra_overtime = start < overtime.start_date or end > overtime.end_date
            else:
                overtime.warning_extra_overtime = False

    def _compute_number_of_hours(self):
        for overtime in self:
            if overtime.end_date and overtime.start_date:
                overtime.number_of_hours = (overtime.end_date - overtime.start_date).total_seconds() / 3600
            else:
                overtime.number_of_hours = False

    @api.model_create_multi
    def create(self, vals_list):
        overtimes = super().create(vals_list)
        self._reevaluate_work_entries()
        return overtimes

    def _create_work_entries(self):
        work_entries_vals_list = []
        for overtime in self.filtered('employee_id'):
            start, end = overtime.start_date, overtime.end_date
            contracts = overtime.employee_id._get_contracts(start, end, states=['open', 'close'])
            for contract in contracts:
                # Generate only if it has already been generated
                if start >= contract.date_generated_from and end <= contract.date_generated_to:
                    work_entries_vals_list += [overtime._get_work_entry_values(contract)]
        return self.env['hr.work.entry'].create(work_entries_vals_list)

    def _get_work_entry_values(self, contract):
        work_entry_type = self.env.ref('hr_payroll_attendance.work_entry_type_overtime', raise_if_not_found=False) or contract._get_default_work_entry_type()
        return {
            'name': "%s: %s" % (work_entry_type.name, contract.employee_id.name),
            'date_start': self.start_date,
            'date_stop': self.end_date,
            'work_entry_type_id': work_entry_type.id,
            'employee_id': contract.employee_id.id,
            'contract_id': contract.id,
            'company_id': contract.company_id.id,
            'state': 'draft',
            'overtime_id': self.id,
        }

    def _update_pending_work_entries(self, **vals):
        vals = {
            field_name: value
            for field_name, value in (vals).items()
            if value is not None
        }
        if vals:
            self.pending_work_entry_ids.write(vals)

    def write(self, vals):
        self._update_pending_work_entries(
            date_start=vals.get('start_date'),
            date_stop=vals.get('end_date'),
        )
        res = super().write(vals)
        if 'employee_id' in vals:
            self.pending_work_entry_ids.unlink()
        self._reevaluate_work_entries()
        return res

    def unlink(self):
        work_entries = self.pending_work_entry_ids
        work_entries.active = False
        return super().unlink()

    def _reevaluate_work_entries(self):
        domain = [('employee_id', '=', self.employee_id.id)]
        domain = expression.AND([domain, [('check_in', '<=', self.start_date), ('check_out', '>=', self.start_date)]])
        domain = expression.OR([domain, [('check_in', '<=', self.end_date), ('check_out', '>=', self.end_date)]])
        attendances = self.env['hr.attendance'].search(domain)

        for attendance in attendances:
            attendance._regenerate_work_entries(attendance.check_in, attendance.check_out)
        attendances._update_work_entries()
