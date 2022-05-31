import base64

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval


class ProvidentFundLine(models.Model):
    _name = 'provident.fund.line'
    _description = 'Provident Fund Line'
    
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    emp_id = fields.Char(related = 'employee_id.emp_id', related_sudo=False, string='Emp ID')
    salary_month = fields.Date('Salary Month', store=True)
    pf_amount = fields.Float(string='PF Amount', store=True)
    month = fields.Char('Month', store=True)
    year = fields.Char('Year', store=True)
    
    
