import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    attDate = fields.Date(string = "Date")
    empID = fields.Char(related = 'employee_id.emp_id', related_sudo=False, string='Emp ID')
    inTime = fields.Float(compute="_calculate_office_start_time", string = "Office In-Time", readonly=True)
    inHour = fields.Float(string = "In-Time", readonly=True)
    inFlag = fields.Char("In-Flag", readonly=True)
    outTime = fields.Float(compute="_calculate_office_end_time", string = "Office Out-Time", readonly=True)
    outHour = fields.Float(string = "Out-Time", readonly=True)
    outFlag = fields.Char("Out-Flag", readonly=True)
    otHours = fields.Float(string = "OT Hours")
    check_in = fields.Datetime(string = 'Check In',default=False, required=False, store=True, copy=True)
    
    def _calculate_ot(self,att_date,emp_id,inTime,outTime,inHour,worked_hours):
         
        att_obj = self.env['hr.attendance']
        
        get_att_data = att_obj.search([('empID', '=', emp_id), ('attDate', '=', att_date)])
        
        activeemplist = self.env['hr.employee'].search([('emp_id', '=', emp_id),
                                                            ('active', '=', True)])
        if activeemplist.isOverTime is True:
            if outTime > 0.0 and worked_hours > (outTime - inTime):
                if inTime > inHour:
                    delta = ((worked_hours - (inTime - inHour)) - (outTime - inTime))
                    #delta = (outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    get_att_data[-1].write({'otHours' : delta})
                else:
                    delta = (worked_hours - (outTime - inTime))
                    #delta = (outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    get_att_data[-1].write({'otHours' : delta})
            else:
                get_att_data[-1].write({'otHours' : False})
        else:
            get_att_data[-1].write({'otHours' : False})
                
    @api.depends('attDate','employee_id')
    def _calculate_office_start_time(self):
        for record in self:
            get_transfer = self.env['shift.transfer'].search([('empid', '=', record.empID),
                                                              ('activationDate', '<=', record.attDate)])
            trans_data = get_transfer.sorted(key = 'activationDate', reverse=True)[:1]
            record.inTime = trans_data.inTime
            
    @api.depends('attDate','employee_id')
    def _calculate_office_end_time(self):
        for record in self:
            get_transfer = self.env['shift.transfer'].search([('empid', '=', record.empID),
                                                              ('activationDate', '<=', record.attDate)])
            trans_data = get_transfer.sorted(key = 'activationDate', reverse=True)[:1]
            record.outTime = trans_data.outTime

    def generate_attdate(self):
        activeemplist = self.env['hr.employee'].search([('active', '=', True)])
        for employeelist in activeemplist:
            att_obj = self.env['hr.attendance']
            dateGenerate = datetime.datetime.now() + timedelta(hours=6)
            get_transfer = self.env['shift.transfer'].search([('empid', '=', employeelist.emp_id),
                                                              ('activationDate', '<=', dateGenerate)])
            trans_data = get_transfer.sorted(key = 'activationDate', reverse=True)[:1]
            
            get_att_date = att_obj.search([('employee_id', '=', employeelist.id), ('attDate', '=', dateGenerate)])
            if len(get_att_date) == 1:
                get_att_date[-1].write({'attDate': dateGenerate,
                                        'inFlag':'A',
                                        'outFlag':'A',
                                        'inTime': trans_data.inTime,
                                        'outTime': trans_data.outTime})
            else:
                att_obj.create({'attDate': dateGenerate,
                                        'employee_id': employeelist.id,
                                        'inFlag':'A',
                                        'outFlag':'A',
                                        'inTime': trans_data.inTime,
                                        'outTime': trans_data.outTime})
                    
    def generateAttFlag(self,emp_id,att_date,office_in_time,in_time,office_out_time,out_time):
        
        att_obj = self.env['hr.attendance']
        shift_record = self.env['shift.transfer'].search([('empid', '=', emp_id),('activationDate', '<=',att_date)])
        shift_data = shift_record.sorted(key = 'activationDate', reverse=True)[:1]
        get_att_data = att_obj.search([('empID', '=', emp_id), ('attDate', '=', att_date)])
        office_in_time = False
        office_in_time = shift_data.graceinTime
        
        def get_sec(time_str):
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + int(s)

        inHour = False
        if in_time:
            inHour = in_time + timedelta(hours=6)
            inHour = inHour.strftime("%H:%M:%S")
            inHour = get_sec(inHour) / 3600
        outHour = False
        if out_time:
            outHour = out_time + timedelta(hours=6)
            outHour = outHour.strftime("%H:%M:%S")
            outHour = get_sec(outHour) / 3600
        
        myfromtime = 0.0
        mytotime = 7.0
        #office_out_time = get_sec(office_out_time) / 3600
        #myfromtime = datetime.strptime('00:00:00','%H:%M:%S').time()
        #mytotime = datetime.strptime('00:00:00','%H:%M:%S').time()
        #raise UserError((office_in_time,office_out_time,inHour,outHour,in_time,out_time))
        if len(get_att_data) == 1:
            if not inHour and not outHour:
                get_att_data[-1].write({'inFlag':'A','outFlag':'A','inHour' : False,'outHour' : False})
            elif inHour and outHour:
                if str(office_in_time)>=str(inHour):
                    get_att_data[-1].write({'inFlag':'P','inHour' : inHour})
                else:
                    get_att_data[-1].write({'inFlag':'L','inHour' : inHour})
                if office_out_time>outHour:
                    if mytotime>=office_out_time:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    elif myfromtime<=outHour and mytotime>=outHour:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                else:
                    get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
            elif inHour and not outHour:
                if str(office_in_time)>=str(inHour):
                    get_att_data[-1].write({'inFlag':'P','inHour' : inHour,'outFlag':'PO','outHour' : False})
                else:
                    get_att_data[-1].write({'inFlag':'L','inHour' : inHour,'outFlag':'PO','outHour' : False})
            elif not inHour and outHour:
                if office_out_time>outHour:
                    if mytotime>=office_out_time:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    elif myfromtime<=outHour and mytotime>=outHour:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                else:
                    get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """ Verifies the validity of the attendance record compared to the others from the same employee.
            For the same employee we must have :
                * maximum 1 "open" attendance record (without check_out)
                * no overlapping time slices with previous employee records
        """
        for attendance in self:
            # we take the latest attendance before our check_in time and check it doesn't overlap with ours
            last_attendance_before_check_in = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<=', attendance.check_in),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            """if last_attendance_before_check_in and last_attendance_before_check_in.check_out and last_attendance_before_check_in.check_out > attendance.check_in:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name,
                    'datetime': format_datetime(self.env, attendance.check_in, dt_format=False),
                })

            if not attendance.check_out:
                # if our attendance is "open" (no check_out), we verify there is no other "open" attendance
                no_check_out_attendances = self.env['hr.attendance'].search([
                    ('employee_id', '=', attendance.employee_id.id),
                    ('check_out', '=', False),
                    ('id', '!=', attendance.id),
                ], order='check_in desc', limit=1)
                if no_check_out_attendances:
                    raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee hasn't checked out since %(datetime)s") % {
                        'empl_name': attendance.employee_id.name,
                        'datetime': format_datetime(self.env, no_check_out_attendances.check_in, dt_format=False),
                    })
            else:"""
                # we verify that the latest attendance with check_in time before our check_out time
                # is the same as the one before our check_in time computed before, otherwise it overlaps
            last_attendance_before_check_out = self.env['hr.attendance'].search([
                ('employee_id', '=', attendance.employee_id.id),
                ('check_in', '<', attendance.check_out),
                ('id', '!=', attendance.id),
            ], order='check_in desc', limit=1)
            if last_attendance_before_check_out and last_attendance_before_check_in != last_attendance_before_check_out:
                raise exceptions.ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name,
                    'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False),
                })