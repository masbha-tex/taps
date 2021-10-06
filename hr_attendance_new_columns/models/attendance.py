import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime

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
                    
    @api.depends('check_in','inTime')
    def _generate_att_flag(self,emp_id,att_date,in_time,office_in_time,out_time,office_out_time):
        att_obj = self.env['hr.attendance']
        shift_record = self.env['shift.transfer'].search([('empid', '=', emp_id),('activationDate', '<=',att_date)])
        shift_data = shift_record.sorted(key = 'activationDate', reverse=True)[:1]
        get_att_data = att_obj.search([('employee_id', '=', emp_id), ('attDate', '=', att_date)])
        if len(get_att_data) == 1:
            if office_in_time>=inHour:
                get_att_data[-1].write({'inFlag':'P'})
            if office_in_time<=inHour:
                get_att_data[-1].write({'inFlag':'L'})
            if not office_out_time:
                if office_in_time:
                    get_att_data[-1].write({'outFlag':'PO'})
                else:
                    get_att_data[-1].write({'outFlag':'A'})
            if office_out_time>=outHour:
                get_att_data[-1].write({'outFlag':'EO'})
            if office_out_time<=outHour:
                get_att_data[-1].write({'outFlag':'TO'})
            
            
            
            
            """get_att_data[-1].write({'attDate': dateGenerate,
                                        'inFlag':'A',
                                        'outFlag':'A',
                                        'inTime': trans_data.inTime,
                                        'outTime': trans_data.outTime})"""