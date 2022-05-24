import pytz
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta

class HrEmployee(models.Model):
    _inherit = 'hr.employee' 
    
    emp_id = fields.Char(string="Emp ID", readonly=True, store=True, tracking=True) 
    isOverTime = fields.Boolean("Over Time", readonly=False, store=True, tracking=True)
    service_length = fields.Char( string="Service Length")#compute='_calculate_serviceLength',
    joining_date = fields.Date(related = 'contract_id.date_start', related_sudo=False, string='Joining Date', store=True, tracking=True)
    probation_date = fields.Date(related = 'contract_id.trial_date_end', related_sudo=False, store=True, tracking=True)
    resign_date = fields.Date(related = 'contract_id.date_end', related_sudo=False, string='Resign Date', store=True, tracking=True)
    grade = fields.Char(related = 'contract_id.structure_type_id.default_struct_id.name', 
                              related_sudo=False, string='Grade', store=True, tracking=True)
    shift_group = fields.Many2one('shift.setup', string="Attendance Group", store=True, tracking=True)
    fathers_name = fields.Char(string="Father's Name", store=True, tracking=True)
    mothers_name = fields.Char(string="Mother's Name", store=True, tracking=True)
    marriageDate = fields.Date(string='Date of Marriages', store=True, tracking=True)

    def name_get(self):
        result = []
        for record in self:
            name = record.emp_id  + ' - ' +  record.name
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('emp_id', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        
    
    def _calculate_serviceLength(self):
        emp_obj = self.env['hr.employee'].search([('active', '=', True)])
        for record in emp_obj:
            if record:
                if record.resign_date:
                    currentDate = fields.datetime.strptime(str(record.resign_date),'%Y-%m-%d')
                else:
                    currentDate = fields.datetime.now()
                if record.joining_date:
                    deadlineDate = fields.datetime.strptime(str(record.joining_date),'%Y-%m-%d')
                else:
                    deadlineDate = fields.datetime.now()
                
                daysLeft = deadlineDate - currentDate
                years = ((daysLeft.total_seconds())/(365.242*24*3600))
                years = abs(years)
                yearsInt=int(years)
                months=(years-yearsInt)*12
                months = abs(months)
                monthsInt=int(months)
                days=(months-monthsInt)*(365.242/12)
                days = abs(days)
                daysInt=int(days)
                length = str(int(yearsInt)) + ' Years ' + str(int(monthsInt)) + ' Months ' + str(int(daysInt)) + ' Days '
            
                record[-1].write({'service_length' : length})
            else:
                record.write({'service_length' : False})
     
    
class TapsHrEmployeeBase(models.AbstractModel):
    _inherit = "hr.employee.base"
    

    attendance_ids = fields.One2many('hr.attendance', 'employee_id', help='list of attendances for the employee')
    last_attendance_id = fields.Many2one('hr.attendance', compute='_compute_last_attendance_id', store=True)
    last_check_in = fields.Datetime(related='last_attendance_id.check_in', store=True)
    last_check_out = fields.Datetime(related='last_attendance_id.check_out', store=True)
    attendance_state = fields.Selection(string="Attendance Status", compute='_compute_attendance_state', selection=[('checked_out', "Checked out"), ('checked_in', "Checked in")])
    hours_last_month = fields.Float(compute='_compute_hours_last_month')
    hours_today = fields.Float(compute='_compute_hours_today')
    hours_last_month_display = fields.Char(compute='_compute_hours_last_month')
         

    @api.depends('user_id.im_status', 'attendance_state')
    def _compute_presence_state(self):
        """
        Override to include checkin/checkout in the presence state
        Attendance has the second highest priority after login
        """
        super()._compute_presence_state()
        employees = self.filtered(lambda e: e.hr_presence_state != 'present')
        employee_to_check_working = self.filtered(lambda e: e.attendance_state == 'checked_out'
                                                            and e.hr_presence_state == 'to_define')
        working_now_list = employee_to_check_working._get_employee_working_now()
        for employee in employees:
            if employee.attendance_state == 'checked_out' and employee.hr_presence_state == 'to_define' and \
                    employee.id not in working_now_list:
                employee.hr_presence_state = 'absent'
            elif employee.attendance_state == 'checked_in':
                employee.hr_presence_state = 'present'

    def _compute_hours_last_month(self):
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            tz = pytz.timezone(employee.tz or 'UTC')
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(months=-1, day=1, hour=0, minute=0, second=0, microsecond=0)
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)
            end_tz = now_tz + relativedelta(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_naive = end_tz.astimezone(pytz.utc).replace(tzinfo=None)

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                '&',
                ('check_in', '<=', end_naive),
                ('check_out', '>=', start_naive),
            ])

            hours = 0
            for attendance in attendances:
                check_in = max(attendance.check_in, start_naive)
                check_out = min(attendance.check_out, end_naive)
                hours += (check_out - check_in).total_seconds() / 3600.0

            employee.hours_last_month = round(hours, 2)
            employee.hours_last_month_display = "%g" % employee.hours_last_month

    def _compute_hours_today(self):
        now = fields.Datetime.now()
        now_utc = pytz.utc.localize(now)
        for employee in self:
            # start of day in the employee's timezone might be the previous day in utc
            tz = pytz.timezone(employee.tz)
            now_tz = now_utc.astimezone(tz)
            start_tz = now_tz + relativedelta(hour=0, minute=0)  # day start in the employee's timezone
            start_naive = start_tz.astimezone(pytz.utc).replace(tzinfo=None)

            attendances = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
                ('check_in', '<=', now),
                '|', ('check_out', '>=', start_naive), ('check_out', '=', False),
            ])

            worked_hours = 0
            for attendance in attendances:
                delta = (attendance.check_out or now) - max(attendance.check_in, start_naive)
                worked_hours += delta.total_seconds() / 3600.0
            employee.hours_today = worked_hours

    @api.depends('attendance_ids')
    def _compute_last_attendance_id(self):
        for employee in self:
            employee.last_attendance_id = self.env['hr.attendance'].search([
                ('employee_id', '=', employee.id),
            ], limit=1)

    @api.depends('last_attendance_id.check_in', 'last_attendance_id.check_out', 'last_attendance_id')
    def _compute_attendance_state(self):
        for employee in self:
            att = employee.last_attendance_id.sudo()
            employee.attendance_state = att and not att.check_out and 'checked_in' or 'checked_out'

    @api.model
#     def attendance_scan(self, barcode):
#         """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
#             Returns either an action or a warning.
#         """
# #         raise UserError(('adad'))
#         employee = self.sudo().search([('barcode', '=', barcode)], limit=1)
# #         raise UserError((employee))
        
#         if employee:
            
#             return employee._attendance_action('taps_hr.action_job_card_kiosk_report', barcode)
#         return {'warning': _("No employee corresponding to Badge ID '%(barcode)s.'") % {'barcode': barcode}}
    def attendance_scan(self, barcode):
        """ Receive a barcode scanned from the Kiosk Mode and change the attendances of corresponding employee.
            Returns either an action or a warning.
        """
        employee = self.sudo().search([('barcode', '=', barcode)], limit=1)
    
        if employee:
            return employee._attendance_action('hr_attendance.hr_attendance_action_kiosk_mode')
        return {'warning': _("No employee corresponding to Badge ID '%(barcode)s.'") % {'barcode': barcode}}

    def attendance_manual(self, next_action, entered_pin=None):
        self.ensure_one()
        can_check_without_pin = not self.env.user.has_group('hr_attendance.group_hr_attendance_use_pin') or (self.user_id == self.env.user and entered_pin is None)
        if can_check_without_pin or entered_pin is not None and entered_pin == self.sudo().pin:
            return self._attendance_action(next_action)
        return {'warning': _('Wrong PIN')}

    def _attendance_action(self, next_action):
        """ Changes the attendance of the employee.
            Returns an action to the check in/out message,
            next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
        """
        def get_sec(time_str):
            h, m= time_str.split(':')
            return int(h) * 3600 + int(m) * 60
        
        self.ensure_one()
        employee = self.sudo()             

        fromdate = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        todate = fields.Date.today().strftime('%Y-%m-25')
#         raise UserError((fromdate,todate,data.get('empID')))  
        att = self.env['hr.attendance'].search([('attDate', '>=', fromdate),('attDate', '<=', todate),('empID', 'like', employee.emp_id)]).sorted(key = 'attDate')
#         raise UserError((employee.emp_id))
        emplist = att.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        
#         raise UserError((employee))
        fst_days = att.sorted(key = 'attDate', reverse=False)[:1]
        lst_days = att.sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
        officein = []
        intime = []
        inflag = []
        officeout = []
        outtime = []
        outflag = []
        othours = []
        
        
        
        all_datelist = []
        dates = []
        #raise UserError((docs.id)) 
        delta = enddate - stdate       # as timedelta
        for i in range(delta.days + 1):
            day = stdate + timedelta(days=i)
            dates = [
                day,
            ]
            all_datelist.append(dates)
        

        allemp_data = []
        lstmonths_data = []
        
        for details in employee:
            otTotal = 0
            for de in att:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
                    officein.append('{0:02.0f}:{1:02.0f}'.format(*divmod(de.inTime * 60, 60)))
                    intime.append('{0:02.0f}:{1:02.0f}'.format(*divmod(de.inHour * 60, 60)))
                    inflag.append(de.inFlag)
                    officeout.append('{0:02.0f}:{1:02.0f}'.format(*divmod(de.outTime * 60, 60)))
                    outtime.append('{0:02.0f}:{1:02.0f}'.format(*divmod(de.outHour * 60, 60)))
                    outflag.append(de.outFlag)
                    othours.append('{0:02.0f}:{1:02.0f}'.format(*divmod(de.otHours * 60, 60)))
            
            emp_data = []
            emp_data = [
#                 fromdate,
#                 todate,
#                 details.id,
#                 details.emp_id,
#                 details.name,
#                 details.department_id.parent_id.name,
#                 details.department_id.name,
#                 details.job_id.name,
                '{0:02.0f}:{1:02.0f}'.format(*divmod(otTotal * 60, 60)),
            ]
            allemp_data.append(emp_data)
            
            lstmonth_data = []
            lstmonth_data = [
                datetime.strptime(todate, '%Y-%m-%d').strftime('%B  %Y'),

                
            ]
            lstmonths_data.append(lstmonth_data)
#         raise UserError((lstmonth_data))
        
        
        
        if employee.user_id:
            modified_attendance = employee.with_user(employee.user_id)._attendance_action_change()
        else:
            modified_attendance = employee._attendance_action_change()
            
        action_message = self.env["ir.actions.actions"]._for_xml_id("hr_attendance.hr_attendance_action_greeting_message")
        action_message['previous_attendance_change_date'] = employee.last_attendance_id and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
        action_message['employee_name'] = employee.name
        action_message['barcode'] = employee.barcode
        action_message['next_action'] = next_action
        action_message['hours_today'] = employee.hours_today        
        action_message['docs'] = att
        action_message['datas'] = allemp_data
        action_message['alldays'] = all_datelist
        action_message['officein'] = officein
        action_message['intime'] = intime
        action_message['inflag'] = inflag        
        action_message['officeout'] = officeout
        action_message['outtime'] = outtime
        action_message['outflag'] = outflag
        action_message['othours'] = othours
        action_message['lstmonths_data'] = lstmonths_data
        
        action_message['attendance'] = modified_attendance.read()[0]
        #raise UserError(('domain'))

        return {'action': action_message}

#     def _attendance_action(self, next_action):
#         """ Changes the attendance of the employee.
#             Returns an action to the check in/out message,
#             next_action defines which menu the check in/out message should return to. ("My Attendances" or "Kiosk Mode")
#         """
#         self.ensure_one()
#         employee = self.sudo()
#         action_message = self.env["ir.actions.actions"]._for_xml_id("hr_attendance.hr_attendance_action_greeting_message")
#         action_message['previous_attendance_change_date'] = employee.last_attendance_id and (employee.last_attendance_id.check_out or employee.last_attendance_id.check_in) or False
#         action_message['employee_name'] = employee.name
#         action_message['barcode'] = employee.barcode
#         action_message['next_action'] = next_action
#         action_message['hours_today'] = employee.hours_today

#         if employee.user_id:
#             modified_attendance = employee.with_user(employee.user_id)._attendance_action_change()
#         else:
#             modified_attendance = employee._attendance_action_change()
#         action_message['attendance'] = modified_attendance.read()[0]
#         return {'action': action_message}

    def _attendance_action_change(self):
        """ Check In/Check Out action
            Check In: create a new attendance record
            Check Out: modify check_out field of appropriate attendance record
        """
        self.ensure_one()
        action_date = fields.Datetime.now()
        fromdate = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        todate = fields.Date.today().strftime('%Y-%m-25')

#         if self.attendance_state != 'checked_in':
#             vals = {
#                 'employee_id': self.id,
#                 'check_in': action_date,
#             }
#             return self.env['hr.attendance'].create(vals)
#         attendance = self.env['hr.attendance'].search([('attDate', '>=', fromdate),('attDate', '<=', todate),('employee_id', '=', self.id)]).sorted(key = 'attDate')
        attendance = self.env['hr.attendance'].search([('employee_id', '=', self.id)])
#         if attendance:
# #             attendance.check_out = action_date
#         else:
#             raise exceptions.UserError(_('Cannot perform check out on %(empl_name)s, could not find corresponding check in. '
#                 'Your attendances have probably been modified manually by human resources.') % {'empl_name': self.sudo().name, })
        return attendance
        

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if 'pin' in groupby or 'pin' in self.env.context.get('group_by', '') or self.env.context.get('no_group_by'):
            raise exceptions.UserError(_('Such grouping is not allowed.'))
        return super(TapsHrEmployeeBase, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)

    def _compute_presence_icon(self):
        res = super()._compute_presence_icon()
        # All employee must chek in or check out. Everybody must have an icon
        employee_to_define = self.filtered(lambda e: e.hr_icon_display == 'presence_undetermined')
        employee_to_define.hr_icon_display = 'presence_to_define'
        return res
