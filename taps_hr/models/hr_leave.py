# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from dateutil.rrule import rrule, DAILY
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression

_logger = logging.getLogger(__name__)

class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    _description = "Time Off"


    def action_approve(self):
        # if validation_type != 'both': this method calls action_validate() below
        if any(holiday.state != 'confirm' for holiday in self):
            raise UserError(_('Time off request must be confirmed ("To Approve") in order to approve it.'))

        current_employee = self.env.user.employee_id
        self.filtered(lambda hol: hol.validation_type == 'both').write({'state': 'validate1', 'first_approver_id': current_employee.id})
        # Post a second message, more verbose than the tracking message
        for holiday in self.filtered(lambda holiday: holiday.employee_id.user_id):
            holiday.message_post(
                body=_(
                    'Your %(leave_type)s planned on %(date)s has been accepted',
                    leave_type=holiday.holiday_status_id.display_name,
                    date=holiday.date_from
                ),
                partner_ids=holiday.employee_id.user_id.partner_id.ids)
        
        self.filtered(lambda hol: not hol.validation_type == 'both').action_validate()
        #raise UserError(('sfe'))
        if not self.env.context.get('leave_fast_create'):
            self.activity_update()
        att_obj = self.env['hr.attendance']
        t_date = self.date_to.date()
        st_date = self.date_from.date()
        endd = (t_date - st_date).days
        #raise UserError(('sfe'))
        #raise UserError((self.employee_id.emp_id,self.mode_company_id.id,self.department_id.id,self.category_id.id))
        if self.holiday_type == "employee":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('empID', '=', self.employee_id.emp_id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                get_att_data.generateAttFlag(get_att_data.empID,get_att_data.attDate,get_att_data.inTime,get_att_data.check_in, get_att_data.outTime,get_att_data.check_out) 
        
        if self.holiday_type == "company":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.company_id', '=', self.mode_company_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for comp in get_att_data:
                    get_att_data.generateAttFlag(comp.empID,comp.attDate,comp.inTime,comp.check_in,comp.outTime,comp.check_out)
        
        if self.holiday_type == "department":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.department_id', '=', self.department_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for dept in get_att_data:
                    get_att_data.generateAttFlag(dept.empID,dept.attDate,dept.inTime,dept.check_in, dept.outTime,dept.check_out)
        
        if self.holiday_type == "category":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.category_ids', '=', self.category_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for cat in get_att_data:
                    get_att_data.generateAttFlag(cat.empID,cat.attDate,cat.inTime,cat.check_in, cat.outTime,cat.check_out)        
        return True
		
    def action_refuse(self):
        current_employee = self.env.user.employee_id
        if any(holiday.state not in ['draft', 'confirm', 'validate', 'validate1'] for holiday in self):
            raise UserError(_('Time off request must be confirmed or validated in order to refuse it.'))

        validated_holidays = self.filtered(lambda hol: hol.state == 'validate1')
        validated_holidays.write({'state': 'refuse', 'first_approver_id': current_employee.id})
        (self - validated_holidays).write({'state': 'refuse', 'second_approver_id': current_employee.id})
        # Delete the meeting
        self.mapped('meeting_id').write({'active': False})
        # If a category that created several holidays, cancel all related
        linked_requests = self.mapped('linked_request_ids')
        if linked_requests:
            linked_requests.action_refuse()
        # Post a second message, more verbose than the tracking message
        for holiday in self:
            if holiday.employee_id.user_id:
                holiday.message_post(
                    body=_('Your %(leave_type)s planned on %(date)s has been refused', leave_type=holiday.holiday_status_id.display_name, date=holiday.date_from),
                    partner_ids=holiday.employee_id.user_id.partner_id.ids)

        self._remove_resource_leave()
        self.activity_update()
        att_obj = self.env['hr.attendance']
        t_date = self.date_to.date()
        st_date = self.date_from.date()
        endd = (t_date - st_date).days
        for d in range(0, endd+1):
            get_att_data = att_obj.search([('empID', '=', self.employee_id.emp_id),
                                           ('attDate', '=', (st_date + timedelta(days=d)))])
            get_att_data.generateAttFlag(get_att_data.empID,get_att_data.attDate,get_att_data.inTime,get_att_data.inHour,
                                         get_att_data.outTime,get_att_data.outHour)        
        return True
    
    def action_validate(self):
        current_employee = self.env.user.employee_id
        leaves = self.filtered(lambda l: l.employee_id and not l.number_of_days)
        if leaves:
            raise ValidationError(_('The following employees are not supposed to work during that period:\n %s') % ','.join(leaves.mapped('employee_id.name')))

        if any(holiday.state not in ['confirm', 'validate1'] and holiday.validation_type != 'no_validation' for holiday in self):
            raise UserError(_('Time off request must be confirmed in order to approve it.'))

        self.write({'state': 'validate'})
        self.filtered(lambda holiday: holiday.validation_type == 'both').write({'second_approver_id': current_employee.id})
        self.filtered(lambda holiday: holiday.validation_type != 'both').write({'first_approver_id': current_employee.id})

        for holiday in self.filtered(lambda holiday: holiday.holiday_type != 'employee'):
            if holiday.holiday_type == 'category':
                employees = holiday.category_id.employee_ids
            elif holiday.holiday_type == 'company':
                employees = self.env['hr.employee'].search([('company_id', '=', holiday.mode_company_id.id)])
            else:
                employees = holiday.department_id.member_ids

            conflicting_leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True
            ).search([
                ('date_from', '<=', holiday.date_to),
                ('date_to', '>', holiday.date_from),
                ('state', 'not in', ['cancel', 'refuse']),
                ('holiday_type', '=', 'employee'),
                ('employee_id', 'in', employees.ids)])

            if conflicting_leaves:
                # YTI: More complex use cases could be managed in master
                if holiday.leave_type_request_unit != 'day' or any(l.leave_type_request_unit == 'hour' for l in conflicting_leaves):
                    raise ValidationError(_('You can not have 2 time off that overlaps on the same day.'))

                # keep track of conflicting leaves states before refusal
                target_states = {l.id: l.state for l in conflicting_leaves}
                conflicting_leaves.action_refuse()
                split_leaves_vals = []
                for conflicting_leave in conflicting_leaves:
                    if conflicting_leave.leave_type_request_unit == 'half_day' and conflicting_leave.request_unit_half:
                        continue

                    # Leaves in days
                    if conflicting_leave.date_from < holiday.date_from:
                        before_leave_vals = conflicting_leave.copy_data({
                            'date_from': conflicting_leave.date_from.date(),
                            'date_to': holiday.date_from.date() + timedelta(days=-1),
                            'state': target_states[conflicting_leave.id],
                        })[0]
                        before_leave = self.env['hr.leave'].new(before_leave_vals)
                        before_leave._compute_date_from_to()

                        # Could happen for part-time contract, that time off is not necessary
                        # anymore.
                        # Imagine you work on monday-wednesday-friday only.
                        # You take a time off on friday.
                        # We create a company time off on friday.
                        # By looking at the last attendance before the company time off
                        # start date to compute the date_to, you would have a date_from > date_to.
                        # Just don't create the leave at that time. That's the reason why we use
                        # new instead of create. As the leave is not actually created yet, the sql
                        # constraint didn't check date_from < date_to yet.
                        if before_leave.date_from < before_leave.date_to:
                            split_leaves_vals.append(before_leave._convert_to_write(before_leave._cache))
                    if conflicting_leave.date_to > holiday.date_to:
                        after_leave_vals = conflicting_leave.copy_data({
                            'date_from': holiday.date_to.date() + timedelta(days=1),
                            'date_to': conflicting_leave.date_to.date(),
                            'state': target_states[conflicting_leave.id],
                        })[0]
                        after_leave = self.env['hr.leave'].new(after_leave_vals)
                        after_leave._compute_date_from_to()
                        # Could happen for part-time contract, that time off is not necessary
                        # anymore.
                        if after_leave.date_from < after_leave.date_to:
                            split_leaves_vals.append(after_leave._convert_to_write(after_leave._cache))

                split_leaves = self.env['hr.leave'].with_context(
                    tracking_disable=True,
                    mail_activity_automation_skip=True,
                    leave_fast_create=True,
                    leave_skip_state_check=True
                ).create(split_leaves_vals)

                split_leaves.filtered(lambda l: l.state in 'validate')._validate_leave_request()

            values = holiday._prepare_employees_holiday_values(employees)
            leaves = self.env['hr.leave'].with_context(
                tracking_disable=True,
                mail_activity_automation_skip=True,
                leave_fast_create=True,
                leave_skip_state_check=True,
            ).create(values)

            leaves._validate_leave_request()

        employee_requests = self.filtered(lambda hol: hol.holiday_type == 'employee')
        employee_requests._validate_leave_request()
        if not self.env.context.get('leave_fast_create'):
            employee_requests.filtered(lambda holiday: holiday.validation_type != 'no_validation').activity_update()
        
        
        t_date = self.date_to.date()
        st_date = self.date_from.date()
        endd = (t_date - st_date).days
        att_obj = self.env['hr.attendance']
        #raise UserError(('sfe'))
        #raise UserError((self.employee_id.emp_id,self.mode_company_id.id,self.department_id.id,self.category_id.id))
        if self.holiday_type == "employee":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('empID', '=', self.employee_id.emp_id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                get_att_data.generateAttFlag(get_att_data.empID,get_att_data.attDate,get_att_data.inTime,get_att_data.check_in, get_att_data.outTime,get_att_data.check_out) 
        
        if self.holiday_type == "company":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.company_id', '=', self.mode_company_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for comp in get_att_data:
                    get_att_data.generateAttFlag(comp.empID,comp.attDate,comp.inTime,comp.check_in,comp.outTime,comp.check_out)
        
        if self.holiday_type == "department":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.department_id', '=', self.department_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for dept in get_att_data:
                    get_att_data.generateAttFlag(dept.empID,dept.attDate,dept.inTime,dept.check_in, dept.outTime,dept.check_out)
        
        if self.holiday_type == "category":
            for d in range(0, endd+1):
                get_att_data = att_obj.search([('employee_id.category_ids', '=', self.category_id.id),
                                               ('attDate', '=', (st_date + timedelta(days=d)))])
                for cat in get_att_data:
                    get_att_data.generateAttFlag(cat.empID,cat.attDate,cat.inTime,cat.check_in, cat.outTime,cat.check_out)        
        return True

#     def _validate_leave_request(self):
#         """ Validate time off requests (holiday_type='employee')
#         by creating a calendar event and a resource time off. """
#         holidays = self.filtered(lambda request: request.holiday_type == 'employee')
#         holidays._create_resource_leave()
#         meeting_holidays = holidays.filtered(lambda l: l.holiday_status_id.create_calendar_meeting)
#         if meeting_holidays:
#             meeting_values = meeting_holidays._prepare_holidays_meeting_values()
#             meetings = self.env['calendar.event'].with_context(
#                 no_mail_to_attendees=True,
#                 active_model=self._name
#             ).create(meeting_values)
#             for holiday, meeting in zip(meeting_holidays, meetings):
#                 holiday.meeting_id = meeting