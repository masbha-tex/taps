from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class EmployeeGroup(models.Model):
    _name = 'hr.employee.group'
    _description = 'Employee Group'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char(string="Group Name", required=True, index=True, translate=True)
    sequence = fields.Integer()
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the Group Name must be unique per Group Name in company!'),]    

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)        

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(EmployeeGroup, self).copy(default=default)