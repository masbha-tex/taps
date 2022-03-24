import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models, _
import math
import pytz

class StockForecastReport(models.TransientModel):
    _name = 'kiosk.jobcard'
    _description = 'KIOSK'
    
    employee_id = fields.Char(string="", required=True)
    attendance_ids = fields.One2many('hr.attendance','id', ondelete='cascade', string='')
    
#     @api.onchange()
    @api.model
    def open_attendance(self):
        data = {'empID': self.empID}
        raise UserError(('fefefe'))
        return self.env.ref('taps_hr.action_job_card_kiosk_report').report_action(self, data=data)
        #fromdate = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        #todate = fields.Date.today().strftime('%Y-%m-25')
    
        #hrattendance = self.env['hr.attendance'].search([('attDate', '>=', fromdate),('attDate', '<=', todate), ('	empID', 'like', empID)]).sorted(key = 'attDate')
        
#         access_kiosk_jobcard,access_kiosk_jobcard,model_kiosk_jobcard,base.group_user,1,1,1,1

class JobCardKiosk(models.AbstractModel):
    _name = 'report.taps_hr.jobcard_kiosk_template'
    _description = 'Kiosk Job Card Template'      
    
    def _get_report_values(self, docids, data=None):
        #raise UserError((domain))    
        fromdate = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26')
        todate = fields.Date.today().strftime('%Y-%m-25')
        docs = self.env['hr.attendance'].search([('attDate', '>=', fromdate),('attDate', '<=', todate),
                                                 ('	empID', 'like', data.get('empID'))]).sorted(key = 'attDate')
        #raise UserError((docs.id)) 
        emplist = docs.mapped('employee_id.id')
        employee = self.env['hr.employee'].search([('id', 'in', (emplist))])
        fst_days = docs.sorted(key = 'attDate', reverse=False)[:1]
        lst_days = docs.sorted(key = 'attDate', reverse=True)[:1]
        
        stdate = fst_days.attDate
        enddate = lst_days.attDate
        
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
        for details in employee:
            otTotal = 0
            for de in docs:
                if details.id == de.employee_id.id:
                    otTotal = otTotal + de.otHours
            
            emp_data = []
            emp_data = [
                fromdate,
                todate,
                details.id,
                details.emp_id,
                details.name,
                details.department_id.parent_id.name,
                details.department_id.name,
                details.job_id.name,
                otTotal,
            ]
            allemp_data.append(emp_data)
        #raise UserError(('domain'))
        return {
            'doc_ids': docs.ids,
            'doc_model': 'hr.attendance',
            'docs': docs,
            'datas': allemp_data,
            'alldays': all_datelist
        }
