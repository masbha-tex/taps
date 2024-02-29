
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError


class HrHealthSafety(models.Model):
    _name = 'hr.health.safety'
    _description = 'Health & Safety'
    _inherit = ['mail.thread', 'mail.activity.mixin']    

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    active = fields.Boolean('Active', default=True)
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)    
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    joining_date = fields.Date(related = 'employee_id.joining_date', related_sudo=False, string='Joining Date', store=True, tracking=True)
    service_length = fields.Char(related = 'employee_id.service_length', related_sudo=False, string='Service Length', store=True)
    accident_date = fields.Date(string = "Date of Accident Occurred")
    shift = fields.Selection(selection=[
        ('1', 'Day'),
        ('2', 'Night')], string="Shift", tracking=True, help="How likely is it that this employee will shift?" )    
    criteria_id = fields.Many2one('hs.criteria', required=True, string='')
    title_ids = fields.Many2one('hs.title', string='Title', required=True, domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
    

    # @api.depends('value')
    # def _value_pc(self):
    #     for record in self:
    #         record.value2 = float(record.value) / 100
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            issue_date = vals.get('issue_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.health.safety', sequence_date=issue_date)
        return super(HrHealthSafety, self).create(vals)
