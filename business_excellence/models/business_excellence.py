
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


class BusinessExcellence(models.Model):
    _name = 'business.excellence'
    _description = 'Business Excellence'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    code = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New'))
    
    parent_project_id = fields.Many2one('business.excellence',
                                       string="Parent Project",
                                       ondelete="cascade",
                                       help="A project will inherit the tags of its parent project")
    name = fields.Char(required=True, translate=True)
    children_project_ids = fields.One2many('business.excellence', 'parent_project_id', string="Sub Project Name")
    # sub_project = fields.Char(string='Project')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    development = fields.Selection(selection=[
        ('1', 'Inhouse'),
        ('2', 'Outsource'),
        ('3', 'Inhouse & Outsource')], string="Development", tracking=True)
    type = fields.Selection([
        ('new', 'New Process'),
        ('existing', 'Existing Process')],string="Type", required=True, default="new")
    currency_id = fields.Many2one('res.currency', string='Currency')
    project_cost= fields.Monetary(string='Project Cost', store=True, currency_field='currency_id')
    date = fields.Date(string = "Start Date")
    finish_date = fields.Date(string = "Finish Date")
    count = fields.Integer(string="Est Days", compute="_compute_count")
    # criteria_id = fields.Many2one('reward.criteria', required=True, string='Title')
    # title_ids = fields.Many2one('reward.title', string='Scope', required=True, domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")

    @api.depends('date', 'finish_date')
    def _compute_count(self):
        for record in self:
            if record.date and record.finish_date:
                count = (record.finish_date - record.date).days
                record.count = count
            else:
                record.count = 0

            
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            date = vals.get('date')
            vals['code'] = self.env['ir.sequence'].next_by_code('business.excellence', sequence_date=date)
        return super(BusinessExcellence, self).create(vals)