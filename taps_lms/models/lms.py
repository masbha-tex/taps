from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta
from odoo.tools.misc import get_lang
import logging
from odoo.tools.profiler import profile

logger = logging.getLogger("*___LMS___*")


class Course(models.Model):
    _name = 'lms.course'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Training Courses'
    _rec_name = 'course_name'

    name = fields.Char(string="Course Number", required=True, index=True, copy=False, readonly=True, default=_('New'))
    course_name = fields.Char(string='Title', required=True, translate=True, tracking=True)
    description = fields.Text('Content', help='Add content description here...')
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True, tracking=True)
    session_ids = fields.One2many('lms.session', 'course_id', string="Sessions")
    state = fields.Selection([('draft', 'Draft'), ('submitted', 'Submitted'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancel', 'Cancel')
                              ], string='Status', readonly=False, tracking=True, default='draft', copy=False)
    course_date = fields.Date('Course date', required=True, default=fields.Date.today())

    def action_submit(self):
        self.state = 'submitted'
        users = self.env.ref('taps_lms.group_course_approval').users
        for user in users:
            self.activity_schedule('taps_lms.mail_act_course_approval', user_id=user.id, note=f'Please Approve Training course {self.name}')

    def name_get(self):
        result = []
        for record in self:
            name = f"[{record.name}] {record.course_name}"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        if not args:
            args = []
        if name:
            course_ids = self._search([('name', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
            if not course_ids:
                course_ids = self._search([('course_name', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
        else:
            course_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
        return course_ids #models.lazy_name_get(self.browse(course_ids).with_user(name_get_uid))

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            course_date = vals.get('course_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('lms.course', sequence_date=course_date)
        return super(Course, self).create(vals)

    def action_validate(self):
        for record in self:
            logger.info(f"Course {record.course_name} state moved to In progress by {self.env.user.name}")
            record.write({'state': 'in_progress'})
            activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id),
                                                            ('activity_type_id', '=', self.env.ref('taps_lms.mail_act_course_approval').id)])
            activity_id.action_feedback(feedback='Approved')
            other_activity_ids = self.env['mail.activity'].search(
                [('res_id', '=', self.id), ('activity_type_id', '=', self.env.ref('taps_lms.mail_act_course_approval').id)])
            other_activity_ids.unlink()

    def action_completed(self):
        for record in self:
            record.write({'state': 'completed'})
            return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Course Completed',
                    'type': 'rainbow_man',
                    'img_url': 'taps_lms/static/img/success.png'
                }
            }

    def action_cancel(self):
        for record in self:
            logger.error(f"Course {record.course_name} state moved to Cancelled by {self.env.user.name}")
            record.write({'state': 'cancel'})

    def copy(self, default=None):
        default = dict(default or {})

        copied_count = self.search_count(
            [(_('course_name', '=like', u"Copy of {}%").format(self.course_name))])
        if not copied_count:
            new_name = u"Copy of {}".format(self.course_name)
        else:
            new_name = u"Copy of {} ({})".format(self.course_name, copied_count)

        default['course_name'] = new_name
        return super(Course, self).copy(default)

    _sql_constraints = [
        ('name_description_check',
         'check (course_name != description)',
         'The course name and description can not be same.'),

        ('course_name_unique',
         'unique(course_name)',
         'Course name should be unique'),
    ]


class Session(models.Model):
    _name = 'lms.session'
    _description = "Training Sessions"

    def get_default_duration(self):
        ICP = self.env['ir.config_parameter'].sudo()
        default_duration = ICP.get_param('taps_lms.session_duration')
        return default_duration

    def get_default_seats(self):
        ICP = self.env['ir.config_parameter'].sudo()
        default_seats = ICP.get_param('taps_lms.session_allowed_seats')
        return default_seats

    @api.onchange('course_id', 'instructor_id')
    def _get_instructor_domain(self):
        # raise UserError((self.course_id.responsible_id.partner_id.id))
        return {'domain': {'instructor_id': [('user_id', '=', self.course_id.responsible_id.id)]}}

    name = fields.Char(string="Venue", required=True)
    start_date = fields.Datetime(string="Plan Date",default=fields.datetime.today())
    duration = fields.Float(digits=(6, 2), help="Duration in hours", default=get_default_duration)
    end_date = fields.Datetime(string="End Date", store=True, compute='_get_end_date', inverse='_set_end_date')
    seats = fields.Integer(string="Number of seats", default=get_default_seats)
    instructor_id = fields.Many2one('hr.employee', string="Facilitator")    
    country_id = fields.Many2one('res.country', related='instructor_id.country_id')
    course_id = fields.Many2one('lms.course', ondelete='cascade', string="Course", required=True)
    attendee_ids = fields.Many2many('hr.employee', string="Attendees")
    taken_seats = fields.Float(string="Taken seats", compute='_taken_seats')
    active = fields.Boolean(string='Active', default=True)
    attendees_count = fields.Integer(
        string="Attendees count", compute='_get_attendees_count', store=True)
    color = fields.Integer()
    email_sent = fields.Boolean('Email Sent', default=False)
    image_1920 = fields.Image("Image")
    attendance_ids = fields.One2many('lms.session.attendance', 'session_id', string="Attendance")
    
    def action_open_barcode_scanner(self):
        action = self.env.ref('taps_lms.action_barcode_scanner').read()[0]
        # action['context'] = {
        #     'active_id': self.id,
        # }
        context = dict(self.env.context, active_id=self.id)
        action['context'] = context
        return action
        # return {
        #     'type': 'ir.actions.client',
        #     'tag': 'taps_lms_barcode_scanner',
        #     'name': 'LMS Attendances',
        #     'target': 'main',
        #     'context': {},
        # }
    
    @api.model
    def attendance_scan(self, barcode, activeId):        
        # active_id = context.get('activeId')
        # active_id = self.env['lms.session'].browse(self.env.context.get('active_id'))
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
        raise UserError((activeId))
        if employee:
            return self._attendance_action('taps_lms.session_list_action',barcode)
        return {'warning': _("No employee corresponding to Badge ID '%(barcode)s.'") % {'barcode': barcode}}

    def attendance_manual(self, next_action, entered_pin=None):
        self.ensure_one()
        employee = self.env['hr.employee']
        attendance_user_and_no_pin = self.user_has_groups(
            'hr_attendance.group_hr_attendance_user,'
            '!hr_attendance.group_hr_attendance_use_pin')
        can_check_without_pin = attendance_user_and_no_pin or (self.user_id == self.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == employee.pin:
            return self._attendance_action(next_action)
        return {'warning': _('Wrong PIN')}

    def _attendance_action(self, next_action, barcode=None):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        # self.ensure_one()
        
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
        action_message = self.env["ir.actions.actions"]._for_xml_id("taps_lms.action_greeting_message")
        action_message['previous_attendance_change_date'] = employee.last_attendance_id and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today

        if employee.user_id:
            
            modified_attendance = self.with_user(employee.user_id)._attendance_action_change(barcode)
        else:
            
            modified_attendance = self._attendance_action_change(barcode)
        action_message['attendance'] = modified_attendance.read()[0]
        # raise UserError((action_message['attendance'].check_in_time))
        return {'action': action_message}

    def _attendance_action_change(self, barcode=None):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        # self.ensure_one()
        employee = self.env['hr.employee'].search([('barcode', '=', barcode)], limit=1)
        action_date = fields.Datetime.now()
        at_date = fields.Date.today()
        # active_session_id = self.env.context.get('active_id')
        # raise UserError((self.env.context.get('default_session_id')))
        # raise UserError((barcode,active_session_id))

        if employee:
            # raise UserError((barcode,'ss'))
            vals = {
                'attDate': at_date,
                'employee_id': employee.id,
                'check_in': action_date,
            }
            return self.env['hr.attendance'].create(vals)
        attendance = self.env['hr.attendance'].search([('attDate', '=', at_date),('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1)
        if attendance:
            attendance.check_out = action_date
        else:
            raise UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
                'Your attendances have probably been modified manually by human resources.') % {'empl_name': employee.name, })
        return attendance
    

    def mark_attendances(self, barcode):
        # raise UserError((barcode))
        attendee = self.env['res.partner'].search([('barcode_id', '=', barcode)], limit=1)
    
        if attendee:
            # Check if an attendance record already exists for the given session and attendee
            existing_attendance = self.env['lms.session.attendance'].search([
                ('session_id', '=', self.id),
                ('attendee_id', '=', attendee.id),
            ], limit=1)
    
            if not existing_attendance:
                # Create a new attendance record if not already present
                self.env['lms.session.attendance'].create({
                    'session_id': self.id,
                    'attendee_id': attendee.id,
                    'barcode_id': barcode,
                })
    
        return {
            'name': "Mark Attendance",
            'view_mode': 'tree,form',
            'res_model': 'lms.session.attendance',
            'type': 'ir.actions.act_window',
            'context': {
                'default_session_id': self.id,
            },
        }     
    def mark_attendance(self):
        # raise UserError((self.env.context.get('default_session_id')))
        # self.ensure_one()
        # attendees = self.attendee_ids.filtered(lambda att: att.active)
        # attendance_vals = []
        # for attendee in attendees:
        #     attendance_vals.append({
        #         'session_id': self.id,
        #         'attendee_id': attendee.id,
        #         'attendance_date': fields.Datetime.today(),
        #         'attended': False,  # You can set this to True if you want to default to attended
        #     })
        # self.env['lms.session.attendance'].create(attendance_vals)
        # return self.action_view_attendance()
        return {
            'name': "Mark Attendance",
            'view_mode': 'tree,form',
            'res_model': 'lms.session.attendance',
            'type': 'ir.actions.act_window',
            'domain': [('session_id', '=', self.id)],
            'context': {
                'default_session_id': self.id,
            },
        }        

    def action_view_attendance(self):
        return {
            'name': "Attendance",
            'view_mode': 'tree,form',
            'res_model': 'lms.session.attendance',
            'type': 'ir.actions.act_window',
            'domain': [('session_id', '=', self.id)],
        }    

    def number_of_attendees(self):
        return len(self.attendee_ids)

    def action_send_session_by_email_cron(self):
        session_ids = self.env['lms.session'].search([('email_sent', '=', False)])
        for session in session_ids:
            if session.email_sent is False:
                session.action_send_session_by_email()
                session.email_sent = True

    @profile()
    def action_send_session_by_email(self):
        # for attendee in self.attendee_ids:
        ctx = {}
        email_list = self.attendee_ids.mapped('email')
        if email_list:
            ctx['email_to'] = ','.join([email for email in email_list if email])
            ctx['email_from'] = self.env.user.company_id.email
            ctx['send_email'] = True
            ctx['attendee'] = ''
            template = self.env.ref('taps_lms.email_template_lms_session')
            template.with_context(ctx).send_mail(self.id, force_send=False, raise_exception=False)

    @api.depends('attendee_ids')
    def _get_attendees_count(self):
        for r in self:
            r.attendees_count = len(r.attendee_ids)

    @api.depends('start_date', 'duration')
    def _get_end_date(self):
        for r in self:
            if not (r.start_date and r.duration):
                r.end_date = r.start_date
                continue

            # Add duration to start_date, but: Monday + 5 days = Saturday, so
            # subtract one second to get on Friday instead
            duration = timedelta(hours=r.duration)
            r.end_date = r.start_date + duration

    def _set_end_date(self):
        for r in self:
            if not (r.start_date and r.end_date):
                continue

            # Compute the difference between dates, but: Friday - Monday = 4 days,
            # so add one day to get 5 days instead
            r.duration = (r.end_date - r.start_date).days + 1

    @api.constrains('instructor_id', 'attendee_ids')
    def _check_instructor_not_in_attendees(self):
        for r in self:
            if r.instructor_id and r.instructor_id in r.attendee_ids:
                raise ValidationError("A session's instructor can't be an attendee")

    @api.depends('seats', 'attendee_ids')
    def _taken_seats(self):
        for r in self:
            if not r.seats:
                r.taken_seats = 0.0
            else:
                r.taken_seats = 100.0 * len(r.attendee_ids) / r.seats

    @api.onchange('seats', 'attendee_ids')
    def _verify_valid_seats(self):
        if self.seats < 0:
            return {
                'warning': {
                    'title': "Incorrect 'seats' value",
                    'message': "The number of available seats may not be negative",
                },
            }
        if self.seats < len(self.attendee_ids):
            return {
                'warning': {
                    'title': "Too many attendees",
                    'message': "Increase seats or remove excess attendees",
                },
            }

class SessionAttendance(models.Model):
    _name = 'lms.session.attendance'
    _description = "Training Session Attendance"

    session_id = fields.Many2one('lms.session', string="Session", required=True, ondelete='cascade')
    attendee_id = fields.Many2one('hr.employee', string="Attendee", required=True)
    attendance_date = fields.Datetime(string="Attendance Date", default=fields.datetime.today(), required=True)
    is_present = fields.Boolean(string="Is Present", default=True)
    session_name = fields.Char(related='session_id.name')
            

