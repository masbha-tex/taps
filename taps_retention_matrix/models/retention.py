import base64
import datetime
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date, format_amount

class RetentionMatrix(models.Model):
    _name = 'retention.matrix'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Retention Matrix'

    name = fields.Char(string="Code", store=True,readonly=True, index=True, default='New')
    employee_id = fields.Many2one('hr.employee', string='Employee', store=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True, required=False)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    color = fields.Integer()
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
    date_from = fields.Date('Date From', required=True, index=True,default=fields.Date.context_today)
    date_to = fields.Date('Date To', required=True, index=True, default=fields.Date.context_today)

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

    @api.model
    def create(self, vals):
        if vals.get('name', 'RM') == 'RM':
            vals['name'] = self.env['ir.sequence'].next_by_code('retention.code')
        return super(RetentionMatrix, self).create(vals)

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        # raise UserError(('efrrgrg'))
        self.check_access_rights('read')
        povalue = 0

        result = {
            'retention_low_low': [],
            'retention_low_medium': [],
            'retention_low_high': [],
            'retention_medium_low': [],
            'retention_medium_medium': [],
            'retention_medium_high': [],
            'retention_high_low': [],
            'retention_high_medium': [],
            'retention_high_high': []
        }
        retention_low_low = self.env['retention.matrix'].search([('impact', '=', '1'), ('risk', '=', '1')])
        retention_low_medium = self.env['retention.matrix'].search([('impact', '=', '2'), ('risk', '=', '1')])
        retention_low_high = self.env['retention.matrix'].search([('impact', '=', '3'), ('risk', '=', '1')])
        retention_medium_low = self.env['retention.matrix'].search([('impact', '=', '1'), ('risk', '=', '2')])
        retention_medium_medium = self.env['retention.matrix'].search([('impact', '=', '2'), ('risk', '=', '2')])
        retention_medium_high = self.env['retention.matrix'].search([('impact', '=', '3'), ('risk', '=', '2')])
        retention_high_low = self.env['retention.matrix'].search([('impact', '=', '1'), ('risk', '=', '3')])
        retention_high_medium = self.env['retention.matrix'].search([('impact', '=', '2'), ('risk', '=', '3')])
        retention_high_high = self.env['retention.matrix'].search([('impact', '=', '3'), ('risk', '=', '3')]) 
        
        retention_record=0
        
        for retention_record in retention_low_low:
            result['retention_low_low'].append(retention_record.employee_id.display_name)
        
        result['retention_low_low'] = '<br/>'.join(result['retention_low_low'])
        
        for retention_record in retention_low_medium:
            result['retention_low_medium'].append(retention_record.employee_id.display_name)
        
        result['retention_low_medium'] = '<br/>'.join(result['retention_low_medium'])

        for retention_record in retention_low_high:
            result['retention_low_high'].append(retention_record.employee_id.display_name)
        
        result['retention_low_high'] = '<br/>'.join(result['retention_low_high'])
        
        for retention_record in retention_medium_low:
            result['retention_medium_low'].append(retention_record.employee_id.display_name)
        
        result['retention_medium_low'] = '<br/>'.join(result['retention_medium_low'])

        for retention_record in retention_medium_medium:
            result['retention_medium_medium'].append(retention_record.employee_id.display_name)
        
        result['retention_medium_medium'] = '<br/>'.join(result['retention_medium_medium'])
        
        for retention_record in retention_medium_high:
            result['retention_medium_high'].append(retention_record.employee_id.display_name)
        
        result['retention_medium_high'] = '<br/>'.join(result['retention_medium_high'])

        for retention_record in retention_high_low:
            result['retention_high_low'].append(retention_record.employee_id.display_name)
        
        result['retention_high_low'] = '<br/>'.join(result['retention_high_low'])
        
        for retention_record in retention_high_medium:
            result['retention_high_medium'].append(retention_record.employee_id.display_name)
        
        result['retention_high_medium'] = '<br/>'.join(result['retention_high_medium'])

        for retention_record in retention_high_high:
            result['retention_high_high'].append(retention_record.employee_id.display_name)
        
        result['retention_high_high'] = '<br/>'.join(result['retention_high_high'])
        
       

        
        



        return result


