import base64

import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _

# from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules

from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date




class RetentionMatrix(models.Model):
    _name = 'retention.matrix'
    _description = 'Retention Matrix'


    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    # company_id = fields.Many2one('res.company',required=True)
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    name = fields.Char('Name', store=True,readonly=True, index=True, copy=False,  )
    color = fields.Integer()
    # retantion_line = fields.One2many('retantion.line', string='Retention Lines',tracking=True, store=True, required=True)
    job_id = fields.Many2one('hr.job', 'Position', store=True, readonly=True, compute='_compute_job_id')
    grade = fields.Many2one('hr.payroll.structure.type', 'Grade', store=True, readonly=True, compute='_compute_job_id')
    risk = fields.Selection(selection=[
        ('1', 'Low-Risk'),
        ('2', 'Medium-Risk'),
        ('3', 'High-Risk')], string="Risk",  help="How likely is it that this employee will leave?" )
    impact = fields.Selection(selection=[
        ('1', 'Low-Impact'),
        ('2', 'Medium-Impact'),
        ('3', 'High-Impact')], string="Impact",  help="What would be the impact of this employee leaving?" ) 
    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(),  store=True, required=True)
    quarter = fields.Selection(selection=[
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4'),], string="Quarter")

    @staticmethod
    def _get_year_list():
        current_year = datetime.date.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 2):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((year_str, year_label))
        return year_options

    @staticmethod
    def _get_default_year():
        current_year = datetime.date.today().year
        return str(current_year)

    @api.depends('employee_id')
    def _compute_job_id(self):
        for line in self.filtered('employee_id'):
            line.job_id = line.employee_id.job_id.id
            line.grade = line.employee_id.contract_id.structure_type_id


# class RetentionMatrixLine(models.Model):
#     _name = 'retention.matrix.line'
#     _description = 'Retention Matrix Line'
           
