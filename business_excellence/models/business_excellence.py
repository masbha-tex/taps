
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


class BusinessExcellence(models.Model):
    _name = 'business.excellence'
    _description = 'Business Excellence'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    active = fields.Boolean('Active', default=True)
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)    
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    date = fields.Date(string = "Date")

            
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            date = vals.get('date')
            vals['name'] = self.env['ir.sequence'].next_by_code('business.excellence', sequence_date=date)
        return super(BusinessExcellence, self).create(vals)