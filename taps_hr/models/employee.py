import pytz
from odoo import models, fields, api
from datetime import timedelta
import datetime
from odoo.tools import format_datetime

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
        for record in self:
            emp_obj = self.env['hr.employee'].search([('emp_id', '=', record.emp_id)])
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
            
                emp_obj[-1].write({'service_length' : length})
            else:
                record.write({'service_length' : False})