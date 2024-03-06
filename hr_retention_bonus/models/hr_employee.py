import pytz
from odoo import models, fields, api, exceptions, _, SUPERUSER_ID
from datetime import date, datetime, time, timedelta
from odoo.exceptions import UserError
from odoo.tools import format_datetime
from dateutil.relativedelta import relativedelta
from werkzeug.urls import url_encode

class HrEmployeePrivate(models.Model):
    _inherit = 'hr.employee'

    def _compute_retention_bonus_scheme(self):
        """This compute the bonus amount and total retention scheme count of an employee.
            """
        self.retention_bonus_scheme_count = self.env['hr.retention.bonus'].sudo().search_count([('employee_id', '=', self.id)])

    retention_bonus_scheme_count = fields.Integer(string="Retention Bonus Scheme Count", compute='_compute_retention_bonus_scheme', groups="hr_retention_bonus.group_manager_retention_bonus,hr_retention_bonus.group_user_retention_bonus")
    
    def write(self, vals):
        res = super(HrEmployeePrivate, self).write(vals)
        if vals.get('active') is True:
            if self.category == 'staff' or self.category == 'expatriate':
                for emp in self:
                    retention_bonus = self.env['hr.retention.bonus'].sudo().search([('employee_id', '=', emp.id), ('active', 'in', (False,True))]).sorted(key = 'id', reverse=True)[:1]
                    retention_bonus_line = self.env['hr.retention.bonus.line'].sudo().search([('employee_id', '=', retention_bonus.employee_id.id), ('active', 'in', (False,True))])
                    if retention_bonus:            
                        retention_bonus.sudo().write({'active': True})
                    if retention_bonus_line:            
                        retention_bonus_line.sudo().write({'active': True})                        
        if vals.get('active') is False:
            if self.category == 'staff' or self.category == 'expatriate':
                for emp in self:
                    retention_bonus = self.env['hr.retention.bonus'].sudo().search([('employee_id', '=', emp.id), ('active', 'in', (False,True))]).sorted(key = 'id', reverse=True)[:1]
                    retention_bonus_line = self.env['hr.retention.bonus.line'].sudo().search([('employee_id', '=', retention_bonus.employee_id.id), ('active', 'in', (False,True))])
                    if retention_bonus:
                        retention_bonus.sudo().write({'active': False})
                    if retention_bonus_line:
                        retention_bonus_line.sudo().write({'active': False})
        return res