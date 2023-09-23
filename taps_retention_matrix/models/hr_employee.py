import pytz
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'
    
        
    @api.model
    def create(self, vals):
        employee = super(HrEmployeePrivate, self).create(vals)
        if employee.id:
            retention = self.env['retention.matrix'].create({'employee_id': employee.id})
        return employee

    def write(self, vals):
        res = super(HrEmployeePrivate, self).write(vals)
        for reten in self:
            retention = self.env['retention.matrix'].search([('employee_id', '=', reten.id), ('active', 'in', (False,True))])
            if retention:
                if vals.get('active') is True:
                    retention.update({'active': True})
                if vals.get('active') is False:
                    retention.update({'active': False})
        return res