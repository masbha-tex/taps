import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime
from odoo.tools import format_datetime
from odoo.exceptions import UserError, ValidationError

class HrAttendance(models.Model):
    _inherit = 'hr.attendance'
    
    attDate = fields.Date(string = "Date")
    empID = fields.Char(related = 'employee_id.x_studio_employee_id', related_sudo=False, string='Emp ID')
    inTime = fields.Float(string = "Office In-Time")
    inHour = fields.Char(string = "In-Time")
    inFlag = fields.Char("In-Flag")
    outTime = fields.Float(string = "Office Out-Time")
    outHour = fields.Char(string = "Out-Time")
    outFlag = fields.Char("Out-Flag")
    otHours = fields.Float(string = "OT Hours")
    check_in = fields.Datetime(string = 'Check In',default=False, required=False, store=True, copy=True)

    def generate_attdate(self):
        activeemplist = self.env['hr.employee'].search([('active', '=', True)])
        for employeelist in activeemplist:
            att_obj = self.env['hr.attendance']
            dateGenerate = datetime.datetime.now() + timedelta(hours=6)
            get_transfer = self.env['shift.transfer'].search([('empid', '=', employeelist.pin),('activationDate', '<=', dateGenerate)])
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
                    
    def generateAttFlag(self,emp_id,att_date,office_in_time,in_time,office_out_time,out_time,):
        
        att_obj = self.env['hr.attendance']
        shift_record = self.env['shift.transfer'].search([('empid', '=', emp_id),('activationDate', '<=',att_date)])
        shift_data = shift_record.sorted(key = 'activationDate', reverse=True)[:1]
        get_att_data = att_obj.search([('empID', '=', emp_id), ('attDate', '=', att_date)])
        
        office_in_time = office_in_time
        inHour = format_datetime(self.env, in_time, dt_format=False)
        inHour = str((inHour[-8:])[:-3])
        office_out_time = office_out_time
        outHour = format_datetime(self.env, out_time, dt_format=False)
        outHour = str((outHour[-8:])[:-3])
        
        if len(get_att_data) == 1:
            if str(office_in_time)>=str(inHour):
                get_att_data[-1].write({'inFlag':'P',
                                       'inHour' : inHour})
            if str(office_in_time)<=str(inHour):
                get_att_data[-1].write({'inFlag':'L',
                                       'inHour' : inHour})
                #raise UserError((office_out_time))
            if outHour==False:
                if inHour:
                    get_att_data[-1].write({'outFlag':'PO'})
                else:
                    get_att_data[-1].write({'outFlag':'A'})
            if str(office_out_time)>=str(outHour):
                get_att_data[-1].write({'outFlag':'EO',
                                       'outHour' : outHour})
            if str(office_out_time)<=str(outHour):
                get_att_data[-1].write({'outFlag':'TO',
                                       'outHour' : outHour})
