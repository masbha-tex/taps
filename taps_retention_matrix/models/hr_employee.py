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
        if not employee.company_id.id == 4:  
            retention = self.env['retention.matrix'].sudo().create({'employee_id': employee.id})
        return employee

    def write(self, vals):
        res = super(HrEmployeePrivate, self).write(vals)
        if not self.company_id.id == 4:
            for reten in self:
                retention = self.env['retention.matrix'].sudo().search([('employee_id', '=', reten.id), ('active', 'in', (False,True))])
                if retention:
                    if vals.get('active') is True:                     
                        retention.sudo().write({'active': True})
                    if vals.get('active') is False:
                        retention.sudo().write({'active': False})
        return res