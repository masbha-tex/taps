
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


class BusinessExcellence(models.Model):
    _name = 'business.excellence'
    _description = 'Business Excellence'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New'))
    
    parent_project_id = fields.Many2one('business.excellence',
                                       string="Project Name",
                                       ondelete="cascade",
                                       help="A project will inherit the tags of its parent project")
    name = fields.Char(required=True, translate=True)
    children_project_ids = fields.One2many('business.excellence', 'parent_project_id', string="Sub Project")
    # sub_project = fields.Char(string='Project')
    active = fields.Boolean('Active', default=True)
    # employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)    
    # company_id = fields.Many2one(related='employee_id.company_id', store=True)
    # department_id = fields.Many2one(related='employee_id.department_id', store=True)
    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    date = fields.Date(string = "Date")

            
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            date = vals.get('date')
            vals['code'] = self.env['ir.sequence'].next_by_code('business.excellence', sequence_date=date)
        return super(BusinessExcellence, self).create(vals)