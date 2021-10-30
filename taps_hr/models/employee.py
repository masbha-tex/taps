import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime
from odoo.tools import format_datetime

class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    
    emp_id = fields.Char(string="Emp ID", readonly=True, store=True) 
    isOverTime = fields.Boolean("Over Time", readonly=False, store=True)
    serviceLength = fields.Char(string="Service Length", readonly=True, store=True)
    joining_date = fields.Date(related = 'contract_id.date_start', related_sudo=False, string='Joining Date', store=True)
    probation_date = fields.Date(related = 'contract_id.trial_date_end', related_sudo=False, store=True)
    resign_date = fields.Date(related = 'contract_id.date_end', related_sudo=False, string='Resign Date', store=True)
    grade = fields.Char(related = 'contract_id.structure_type_id.default_struct_id.name', 
                              related_sudo=False, string='Grade', store=True)
    shift_group = fields.Many2one('shift.setup', string="Attendance Group", store=True)
    fathers_name = fields.Char(string="Father's Name's", store=True)
    mothers_name = fields.Char(string="Mother's Name's", store=True)
    marriageDate = fields.Date(string='Date of Marriages', store=True)
    
    
    def _calculate_serviceLength(self,employee_id,join_date,leaving_date):
        
        emp_obj = self.env['hr.employee'].search([('emp_id', '=', employee_id),
                                                            ('active', '=', True)])
        if emp_obj:
            if leaving_date:
                currentDate = datetime.datetime.strptime(str(leaving_date),'%Y-%m-%d')
            else:
                currentDate = datetime.datetime.now()
            if join_date:
                deadlineDate = datetime.datetime.strptime(str(join_date),'%Y-%m-%d')
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