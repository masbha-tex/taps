# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pytz
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext, is_html_empty, email_normalize
from odoo.addons.microsoft_calendar.utils.event_id_storage import combine_ids

class Meeting(models.Model):
    _name = 'calendar.event'
    _inherit = ['calendar.event', 'microsoft.calendar.sync']

    optional_attendee_ids = fields.Many2many('res.partner','lms_session_optional_attendee_rel','event_id', 'partner_id', string="Optional Participants")
    description = fields.Html('Description')

    def _microsoft_values(self, fields_to_sync, initial_values={}):
        values = dict(initial_values)
        if not fields_to_sync:
            return values

        microsoft_guid = self.env['ir.config_parameter'].sudo().get_param('microsoft_calendar.microsoft_guid', False)

        if self.microsoft_recurrence_master_id and 'type' not in values:
            values['seriesMasterId'] = self.microsoft_recurrence_master_id
            values['type'] = 'exception'

        if 'name' in fields_to_sync:
            values['subject'] = self.name or ''

        if 'description' in fields_to_sync:
            values['body'] = {
                # 'content': html2plaintext(self.description) if not is_html_empty(self.description) else '',
                # 'contentType': "text",
                'content': self.description, 
                'contentType': "html",
            }

        if any(x in fields_to_sync for x in ['allday', 'start', 'date_end', 'stop']):
            if self.allday:
                start = {'dateTime': self.start_date.isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': (self.stop_date + relativedelta(days=1)).isoformat(), 'timeZone': 'Europe/London'}
            else:
                start = {'dateTime': pytz.utc.localize(self.start).isoformat(), 'timeZone': 'Europe/London'}
                end = {'dateTime': pytz.utc.localize(self.stop).isoformat(), 'timeZone': 'Europe/London'}

            values['start'] = start
            values['end'] = end
            values['isAllDay'] = self.allday

        if 'location' in fields_to_sync:
            values['location'] = {'displayName': self.location or ''}

        if 'alarm_ids' in fields_to_sync:
            alarm_id = self.alarm_ids.filtered(lambda a: a.alarm_type == 'notification')[:1]
            values['isReminderOn'] = bool(alarm_id)
            values['reminderMinutesBeforeStart'] = alarm_id.duration_minutes

        if 'user_id' in fields_to_sync:
            values['organizer'] = {'emailAddress': {'address': self.user_id.email or '', 'name': self.user_id.display_name or ''}}
            values['isOrganizer'] = self.user_id == self.env.user

        if 'attendee_ids' in fields_to_sync:
            # attendees = self.attendee_ids.filtered(lambda att: att.partner_id not in self.user_id.partner_id)
            # values['attendees'] = [
            #     {
            #         'emailAddress': {'address': attendee.email or '', 'name': attendee.display_name or ''},
            #         'status': {'response': self._get_attendee_status_o2m(attendee)}
            #     } for attendee in attendees]
            attendees = self.attendee_ids.filtered(lambda att: att.partner_id not in self.user_id.partner_id)
            
            # Initialize lists for "Required" and "Optional" attendees
            required_attendees = []
            for attendee in attendees:
                role = "Required"
                attendee_dict = {
                    'emailAddress': {'address': attendee.email or '', 'name': attendee.display_name or ''},
                    'status': {'response': self._get_attendee_status_o2m(attendee)},
                    'type': role
                }
        
                # Append the attendee to the appropriate list
                if role == "Required":
                    required_attendees.append(attendee_dict)
                    

            op_attendees = self.optional_attendee_ids.filtered(lambda att: att.email not in self.user_id.partner_id.mapped('email'))
            optional_attendees = []
            
            for attendee in op_attendees:
                role = "Optional"
                attendee_dict = {
                    'emailAddress': {'address': attendee.email or '', 'name': attendee.display_name or ''},
                    'type': role
                }
                # Append the attendee to the appropriate list
                if role == "Optional":
                    optional_attendees.append(attendee_dict)                    
            # Add both "Required" and "Optional" attendees to the values dictionary
            values['attendees'] = required_attendees + optional_attendees

        if 'privacy' in fields_to_sync or 'show_as' in fields_to_sync:
            values['showAs'] = self.show_as
            sensitivity_o2m = {
                'public': 'normal',
                'private': 'private',
                'confidential': 'confidential',
            }
            values['sensitivity'] = sensitivity_o2m.get(self.privacy)

        if 'active' in fields_to_sync and not self.active:
            values['isCancelled'] = True

        if values.get('type') == 'seriesMaster':
            recurrence = self.recurrence_id
            pattern = {
                'interval': recurrence.interval
            }
            if recurrence.rrule_type in ['daily', 'weekly']:
                pattern['type'] = recurrence.rrule_type
            else:
                prefix = 'absolute' if recurrence.month_by == 'date' else 'relative'
                pattern['type'] = recurrence.rrule_type and prefix + recurrence.rrule_type.capitalize()

            if recurrence.month_by == 'date':
                pattern['dayOfMonth'] = recurrence.day

            if recurrence.month_by == 'day' or recurrence.rrule_type == 'weekly':
                pattern['daysOfWeek'] = [
                    weekday_name for weekday_name, weekday in {
                        'monday': recurrence.mo,
                        'tuesday': recurrence.tu,
                        'wednesday': recurrence.we,
                        'thursday': recurrence.th,
                        'friday': recurrence.fr,
                        'saturday': recurrence.sa,
                        'sunday': recurrence.su,
                    }.items() if weekday]
                pattern['firstDayOfWeek'] = 'sunday'

            if recurrence.rrule_type == 'monthly' and recurrence.month_by == 'day':
                byday_selection = {
                    '1': 'first',
                    '2': 'second',
                    '3': 'third',
                    '4': 'fourth',
                    '-1': 'last',
                }
                pattern['index'] = byday_selection[recurrence.byday]

            dtstart = recurrence.dtstart or fields.Datetime.now()
            rule_range = {
                'startDate': (dtstart.date()).isoformat()
            }

            if recurrence.end_type == 'count':  # e.g. stop after X occurence
                rule_range['numberOfOccurrences'] = min(recurrence.count, MAX_RECURRENT_EVENT)
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'forever':
                rule_range['numberOfOccurrences'] = MAX_RECURRENT_EVENT
                rule_range['type'] = 'numbered'
            elif recurrence.end_type == 'end_date':  # e.g. stop after 12/10/2020
                rule_range['endDate'] = recurrence.until.isoformat()
                rule_range['type'] = 'endDate'

            values['recurrence'] = {
                'pattern': pattern,
                'range': rule_range
            }

        return values

