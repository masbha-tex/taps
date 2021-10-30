import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime
from odoo.tools import format_datetime

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    emp_id = fields.Char(string="Emp ID", readonly=True, store=True, tracking=True) 
    isOverTime = fields.Boolean("Over Time", readonly=False, store=True, tracking=True)
    serviceLength = fields.Char(compute='_calculate_serviceLength', string="Service Length", readonly=True, store=True, tracking=True)
    joining_date = fields.Date(related = 'contract_id.date_start', related_sudo=False, string='Joining Date', store=True, tracking=True)
    probation_date = fields.Date(related = 'contract_id.trial_date_end', related_sudo=False, store=True, tracking=True)
    resign_date = fields.Date(related = 'contract_id.date_end', related_sudo=False, string='Resign Date', store=True, tracking=True)
    grade = fields.Char(related = 'contract_id.structure_type_id.default_struct_id.name', 
                              related_sudo=False, string='Grade', store=True, tracking=True)
    shift_group = fields.Many2one('shift.setup', string="Attendance Group", store=True, tracking=True)
    fathers_name = fields.Char(string="Father's Name's", store=True, tracking=True)
    mothers_name = fields.Char(string="Mother's Name's", store=True, tracking=True)
    marriageDate = fields.Date(string='Date of Marriages', store=True, tracking=True)
    
    #_calculate_serviceLength(record.emp_id,record.joining_date,record.resign_date)
    def _calculate_serviceLength(self):
        emp_obj = self.env['hr.employee'].search([('emp_id', '=', record.emp_id),
                                                            ('active', '=', True)])
        if emp_obj:
            if record.resign_date:
                currentDate = datetime.datetime.strptime(str(record.resign_date),'%Y-%m-%d')
            else:
                currentDate = datetime.datetime.now()
            if record.joining_date:
                deadlineDate = datetime.datetime.strptime(str(record.joining_date),'%Y-%m-%d')
            else:
                deadlineDate = datetime.datetime.now()
                
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
            
            emp_obj[-1].write({'serviceLength' : length})
        else:
            emp_obj[-1].write({'serviceLength' : False})