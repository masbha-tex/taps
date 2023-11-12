# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging
import pytz
from datetime import datetime
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import html2plaintext, plaintext2html, is_html_empty, email_normalize
from odoo.addons.microsoft_calendar.utils.event_id_storage import combine_ids

ATTENDEE_CONVERTER_O2M = {
    'needsAction': 'notresponded',
    'tentative': 'tentativelyaccepted',
    'declined': 'declined',
    'accepted': 'accepted'
}
ATTENDEE_CONVERTER_M2O = {
    'none': 'needsAction',
    'notResponded': 'needsAction',
    'tentativelyAccepted': 'tentative',
    'declined': 'declined',
    'accepted': 'accepted',
    'organizer': 'accepted',
}

class Meeting(models.Model):
    _name = 'calendar.event'
    _inherit = ['calendar.event', 'microsoft.calendar.sync']

    optional_attendee_ids = fields.Many2many('res.partner','lms_session_optional_attendee_rel','event_id', 'partner_id', string="Optional Participants")
    description = fields.Html('Description')

    @api.model
    def _microsoft_to_odoo_values(self, microsoft_event, default_reminders=(), default_values=None, with_ids=False):
        if microsoft_event.is_cancelled():
            return {'active': False}

        sensitivity_o2m = {
            'normal': 'public',
            'private': 'private',
            'confidential': 'confidential',
        }
        
        commands_attendee, commands_required_partner, commands_optional_partner = self._odoo_attendee_commands_m(microsoft_event)
        timeZone_start = pytz.timezone(microsoft_event.start.get('timeZone'))
        timeZone_stop = pytz.timezone(microsoft_event.end.get('timeZone'))
        start = parse(microsoft_event.start.get('dateTime')).astimezone(timeZone_start).replace(tzinfo=None)
        if microsoft_event.isAllDay:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None) - relativedelta(days=1)
        else:
            stop = parse(microsoft_event.end.get('dateTime')).astimezone(timeZone_stop).replace(tzinfo=None)
        values = default_values or {}
        values.update({
            'name': microsoft_event.subject or _("(No title)"),
            # 'description': microsoft_event.body and plaintext2html(microsoft_event.body['content']),
            'description': microsoft_event.body and ('<html>%s</html>' % microsoft_event.body['content']) or False,
            'location': microsoft_event.location and microsoft_event.location.get('displayName') or False,
            'user_id': microsoft_event.owner_id(self.env),
            'privacy': sensitivity_o2m.get(microsoft_event.sensitivity, self.default_get(['privacy'])['privacy']),
            'attendee_ids': commands_attendee,
            'allday': microsoft_event.isAllDay,
            'start': start,
            'stop': stop,
            'show_as': 'free' if microsoft_event.showAs == 'free' else 'busy',
            'recurrency': microsoft_event.is_recurrent()
        })
        if commands_required_partner:
            # Add partner_commands only if set from Microsoft. The write method on calendar_events will
            # override attendee commands if the partner_ids command is set but empty.
            values['partner_ids'] = commands_required_partner
        if commands_optional_partner:
            # Add optional_partner_commands only if set from Microsoft. The write method on calendar_events will
            # override attendee commands if the optional_attendee_ids command is set but empty.
            values['optional_attendee_ids'] = commands_optional_partner            

        if microsoft_event.is_recurrent() and not microsoft_event.is_recurrence():
            # Propagate the follow_recurrence according to the Outlook result
            values['follow_recurrence'] = not microsoft_event.is_recurrence_outlier()

        if with_ids:
            values['microsoft_id'] = combine_ids(microsoft_event.id, microsoft_event.iCalUId)

        if microsoft_event.is_recurrent():
            values['microsoft_recurrence_master_id'] = microsoft_event.seriesMasterId

        alarm_commands = self._odoo_reminders_commands_m(microsoft_event)
        if alarm_commands:
            values['alarm_ids'] = alarm_commands

        return values

    @api.model
    def _odoo_attendee_commands_m(self, microsoft_event):
        commands_attendee = []
        # commands_partner = []
        commands_required_partner = []
        commands_optional_partner = []        

        microsoft_attendees = microsoft_event.attendees or []
        emails = [
            a.get('emailAddress').get('address')
            for a in microsoft_attendees
            if email_normalize(a.get('emailAddress').get('address'))
        ]
        existing_attendees = self.env['calendar.attendee']
        if microsoft_event.match_with_odoo_events(self.env):
            existing_attendees = self.env['calendar.attendee'].search([
                ('event_id', '=', microsoft_event.odoo_id(self.env)),
                ('email', 'in', emails)])
        elif self.env.user.partner_id.email not in emails:
            commands_attendee += [(0, 0, {'state': 'accepted', 'partner_id': self.env.user.partner_id.id, 'role':'Required'})]
            commands_required_partner += [(4, self.env.user.partner_id.id)]
        partners = self.env['mail.thread']._mail_find_partner_from_emails(emails, records=self, force_create=True)
        attendees_by_emails = {a.email: a for a in existing_attendees}
        for email, partner, attendee_info in zip(emails, partners, microsoft_attendees):
            state = ATTENDEE_CONVERTER_M2O.get(attendee_info.get('status').get('response'), 'needsAction')
            # Categorize partners based on role (required or optional)
            role = attendee_info.get('type', '').lower()  # Assuming 'type' indicates the role in Microsoft Graph API
    
            if email in attendees_by_emails:
                # Update existing attendees
                commands_attendee += [(1, attendees_by_emails[email].id, {'state': state, 'role': role})]
            else:
                # Create new attendees
                commands_attendee += [(0, 0, {'state': state, 'partner_id': partner.id, 'role': role})]
    
                if role == "required":
                    commands_required_partner += [(4, partner.id)]
                elif role == "optional":
                    commands_optional_partner += [(4, partner.id)]                
    
                if attendee_info.get('emailAddress').get('name') and not partner.name:
                    partner.name = attendee_info.get('emailAddress').get('name')
    
        for odoo_attendee in attendees_by_emails.values():          
            # Remove old attendees
            if odoo_attendee.email not in emails:
                commands_attendee += [(2, odoo_attendee.id)]
                
                # Separate partners based on some condition
                if odoo_attendee.role == "required":
                    commands_required_partner += [(3, odoo_attendee.partner_id.id)]
                elif odoo_attendee.role == "optional":
                    commands_optional_partner += [(3, odoo_attendee.partner_id.id)]
    
        return commands_attendee, commands_required_partner, commands_optional_partner

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

    # def write(self, values):
    #     update_alarms = False
    #     if 'partner_ids' in values:
    #         values['attendee_ids'] = self._attendees_values(values['partner_ids'])
    #         update_alarms = True
    #     if 'optional_attendee_ids' in values:
    #         values['attendee_ids'] += self._attendees_values(values['optional_attendee_ids'])
    #         update_alarms = True        

    #     previous_attendees = self.attendee_ids

    #     super().write(values)

    #     current_attendees = self.filtered('active').attendee_ids
    #     if 'optional_attendee_ids' in values:
    #         (current_attendees - previous_attendees)._send_mail_to_attendees('calendar.calendar_template_meeting_invitation')

    #     return True

