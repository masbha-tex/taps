import pytz
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
import datetime
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta

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
        
        holiday_record = self.env['resource.calendar.leaves'].search([('resource_id', '=', False),('date_from', '<=', att_date),('date_to', '>=', att_date)])
        
        lv_record = self.env['hr.leave'].search([('employee_id', '=', int(get_att_data.employee_id)),('state', '=', 'validate'),('request_date_from', '<=', att_date),('request_date_to', '>=', att_date)])
        lv_type = self.env['hr.leave.type'].search([('id', '=', int(lv_record.holiday_status_id))])        
        
        if activeemplist.isOverTime is True:
            if get_att_data.outHour > outTime:
                if inTime > inHour:
                    delta = (get_att_data.outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    if (int(att_date.strftime("%w")))==5 or len(holiday_record)==1:
                        delta = worked_hours+0.01999
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600
                    if lv_type.code == 'CO':
                        delta = (get_att_data.outHour - outTime)
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600                        
                    if delta > 0:
                        get_att_data[-1].write({'otHours' : delta})
                    else:
                        get_att_data[-1].write({'otHours' : False})                        
                else:
                    delta = (get_att_data.outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    if (int(att_date.strftime("%w")))==5 or len(holiday_record)==1:
                        delta = worked_hours+0.01999
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600
                    if lv_type.code == 'CO':
                        delta = (get_att_data.outHour - outTime)
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600                        
                    if delta > 0:
                        get_att_data[-1].write({'otHours' : delta})
                    else:
                        get_att_data[-1].write({'otHours' : False})                        
            else:
                if worked_hours > 4.0:
                    delta = (get_att_data.outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    if (int(att_date.strftime("%w")))==5 or len(holiday_record)==1:
                        delta = worked_hours+0.01999
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600
                    if lv_type.code == 'CO':
                        delta = (get_att_data.outHour - outTime)
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600                        
                    if delta > 0:
                        get_att_data[-1].write({'otHours' : delta})
                    else:
                        get_att_data[-1].write({'otHours' : False})                        
                else:
                    delta = (get_att_data.outHour - outTime)
                    delta = (delta * 3600 / 60) / 30
                    delta = int(delta) * 30 * 60 / 3600
                    if (int(att_date.strftime("%w")))==5 or len(holiday_record)==1:
                        delta = worked_hours+0.01999
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600
                    if lv_type.code == 'CO':
                        delta = (get_att_data.outHour - outTime)
                        delta = (delta * 3600 / 60) / 30
                        delta = int(delta) * 30 * 60 / 3600                        
                    if delta > 0:
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
                                        'inTime': trans_data.inTime,
                                        'outTime': trans_data.outTime})
                self.generateAttFlag(get_att_date.empID,get_att_date.attDate,get_att_date.inTime,get_att_date.inHour,
                                     get_att_date.outTime,get_att_date.outHour)
            else:
                att_obj.create({'attDate': dateGenerate,
                                'employee_id': employeelist.id,
                                'inTime': trans_data.inTime,
                                'outTime': trans_data.outTime})
                self.generateAttFlag(att_obj.empID,dateGenerate,att_obj.inTime,att_obj.inHour,att_obj.outTime,att_obj.outHour)
            
                    
    def generateAttFlag(self,emp_id,att_date,office_in_time,in_time,office_out_time,out_time):
        
        att_obj = self.env['hr.attendance']
        shift_record = self.env['shift.transfer'].search([('empid', '=', emp_id),('activationDate', '<=',att_date)])
        shift_data = shift_record.sorted(key = 'activationDate', reverse=True)[:1]
        get_att_data = att_obj.search([('empID', '=', emp_id), ('attDate', '=', att_date)])
        office_in_time = False
        office_in_time = shift_data.graceinTime+0.01999
        lv_record = self.env['hr.leave'].search([('employee_id', '=', int(get_att_data.employee_id)),('state', '=', 'validate'),('request_date_from', '<=', att_date),('request_date_to', '>=', att_date)])
        lv_type = self.env['hr.leave.type'].search([('id', '=', int(lv_record.holiday_status_id))])
        
        holiday_record = self.env['resource.calendar.leaves'].search([('resource_id', '=', False),('date_from', '<=', att_date),('date_to', '>=', att_date)])
        holiday_type = self.env['hr.work.entry.type'].search([('id', '=', int(holiday_record.work_entry_type_id))])
        #,(att_date, 'between','request_date_from and request_date_to')
        #lv_emp = lv_record.filtered(lambda lv: att_date>=lv.request_date_from and att_date<=lv.request_date_to)
        #raise UserError((att_date,get_att_data.employee_id.joining_date))
        def get_sec(time_str):
            h, m= time_str.split(':')
            return int(h) * 3600 + int(m) * 60

        inHour = False
        if in_time:
            inHour = in_time + timedelta(hours=6)
            inHour = inHour.strftime("%H:%M")
            inHour = get_sec(inHour) / 3600
        outHour = False
        if out_time:
            outHour = out_time + timedelta(hours=6)
            outHour = outHour.strftime("%H:%M")
            outHour = get_sec(outHour) / 3600
        
        myfromtime = 0.0
        mytotime = 7.0
      
        t_date = att_date      
        st_date = t_date
        delta = t_date.replace(day=26).day - t_date.day
        if delta<=0:
            st_date = t_date.replace(day=26)
        else:
            st_date = t_date.replace(day=26) - relativedelta(months = 1)
        endd = (t_date - st_date).days
        attdate = t_date - timedelta(days=1)
        get_pre_att_data = att_obj.search([('empID', '=', emp_id), ('attDate', '=', attdate)])

        if len(get_att_data) == 1:
            if get_att_data.employee_id.joining_date and get_att_data.employee_id.joining_date > att_date:
                if len(get_pre_att_data) == 0:
                    for d in range(0, endd):
                        get_pre_att_data.create({'attDate':st_date + timedelta(days=d), 
                                                 'inFlag':'X','outFlag':'X','inHour' : False,'outHour' : False})
        if len(get_att_data) == 1:
            if not inHour and not outHour:
                get_att_data[-1].write({'inFlag':'A','outFlag':'A','inHour' : False,'outHour' : False})
                if (int(att_date.strftime("%w")))==5:
                    get_att_data[-1].write({'inFlag':'F','outFlag':'F','inHour' : False,'outHour' : False})
                if len(holiday_record) == 1:
                    get_att_data[-1].write({'inFlag':holiday_type.code,'outFlag':holiday_type.code,'inHour' : False,'outHour' : False})
                if len(lv_record) == 1:
                    if lv_type.code == 'CO' and (int(att_date.strftime("%w")))==5:
                        get_att_data[-1].write({'inFlag':'F','outFlag':'F','inHour' : False,'outHour' : False})
                    else:
                        if lv_type.code == 'H' and (int(att_date.strftime("%w")))==5:
                            get_att_data[-1].write({'inFlag':'H','outFlag':'H','inHour' : False,'outHour' : False})
                        else:
                            get_att_data[-1].write({'inFlag':lv_type.code,'outFlag':lv_type.code,'inHour' : False,'outHour' : False})
            if inHour and outHour:
                if office_in_time>=inHour:
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
                if (int(att_date.strftime("%w")))==5:
                    get_att_data[-1].write({'inFlag':'FP','inHour' : inHour})
                    if office_out_time>outHour:
                        if mytotime>=office_out_time:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                        elif myfromtime<=outHour and mytotime>=outHour:
                            get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                        else:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                if len(holiday_record) == 1:
                    get_att_data[-1].write({'inFlag':'HP','inHour' : inHour})
                    if office_out_time>outHour:
                        if mytotime>=office_out_time:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                        elif myfromtime<=outHour and mytotime>=outHour:
                            get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                        else:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                if len(lv_record) == 1:
                    get_att_data[-1].write({'inFlag':lv_type.code,'inHour' : inHour})
                    if office_out_time>outHour:
                        if mytotime>=office_out_time:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                        elif myfromtime<=outHour and mytotime>=outHour:
                            get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                        else:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})                        
                if lv_type.code == 'CO':
                    get_att_data[-1].write({'inFlag':'CO','inHour' : inHour})
                    if office_out_time>outHour:
                        if mytotime>=office_out_time:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                        elif myfromtime<=outHour and mytotime>=outHour:
                            get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
                        else:
                            get_att_data[-1].write({'outFlag':'EO','outHour' : outHour})
                    else:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
            if inHour and not outHour:
                if office_in_time>=inHour:
                    get_att_data[-1].write({'inFlag':'P','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if (int(att_date.strftime("%w")))==5:
                        get_att_data[-1].write({'inFlag':'FP','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if len(holiday_record) == 1:
                        get_att_data[-1].write({'inFlag':'HP','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if len(lv_record) == 1:
                        get_att_data[-1].write({'inFlag':lv_type.code,'inHour' : inHour,'outFlag':lv_type.code,'outHour' : False})
                    if lv_type.code == 'CO':
                        get_att_data[-1].write({'inFlag':'CO','inHour' : inHour,'outFlag':'PO','outHour' : False})
                else:
                    get_att_data[-1].write({'inFlag':'L','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if (int(att_date.strftime("%w")))==5:
                        get_att_data[-1].write({'inFlag':'FP','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if len(holiday_record) == 1:
                        get_att_data[-1].write({'inFlag':'HP','inHour' : inHour,'outFlag':'PO','outHour' : False})
                    if len(lv_record) == 1:
                        get_att_data[-1].write({'inFlag':lv_type.code,'inHour' : inHour,'outFlag':lv_type.code,'outHour' : False})
                    if lv_type.code == 'CO':
                        get_att_data[-1].write({'inFlag':'CO','inHour' : inHour,'outFlag':'PO','outHour' : False})                    
            if not inHour and outHour:
                if office_out_time>outHour:
                    if mytotime>=office_out_time:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour,'inHour' : False})
                    elif myfromtime<=outHour and mytotime>=outHour:
                        get_att_data[-1].write({'outFlag':'TO','outHour' : outHour,'inHour' : False})
                    else:
                        get_att_data[-1].write({'outFlag':'EO','outHour' : outHour,'inHour' : False})                
                #if (int(att_date.strftime("%w")))==5:
                    #get_att_data[-1].write({'outFlag':'FP','outHour' : outHour,'inHour' : False})
                #if len(holiday_record) == 1:
                    #get_att_data[-1].write({'outFlag':'HP','outHour' : outHour,'inHour' : False})
                #if len(lv_record) == 1:
                    #get_att_data[-1].write({'outFlag':lv_type.code,'outHour' : outHour,'inHour' : False})                    
                #if lv_type.code == 'CO':
                    #get_att_data[-1].write({'outFlag':'CO','outHour' : outHour,'inHour' : False})                   
                else:
                    get_att_data[-1].write({'outFlag':'TO','outHour' : outHour})
            if get_att_data.employee_id.joining_date and get_att_data.employee_id.joining_date > att_date:
                get_att_data[-1].write({'inFlag':'X','outFlag':'X','inHour' : False,'outHour' : False})            
            if get_att_data.employee_id.resign_date and get_att_data.employee_id.resign_date <= att_date:
                get_att_data[-1].write({'inFlag':'R','outFlag':'R','inHour' : False,'outHour' : False})                    

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
                raise ValidationError(_("Cannot create new attendance record for %(empl_name)s, the employee was already checked in on %(datetime)s") % {
                    'empl_name': attendance.employee_id.name,
                    'datetime': format_datetime(self.env, last_attendance_before_check_out.check_in, dt_format=False),
                })
