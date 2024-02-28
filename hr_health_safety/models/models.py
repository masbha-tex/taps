
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError


class HrHealthSafety(models.Model):
    _name = 'hr.health_safety'
    _description = 'Health & Safety'

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
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
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.health_safety', sequence_date=issue_date)
        return super(HrHealthSafety, self).create(vals)
