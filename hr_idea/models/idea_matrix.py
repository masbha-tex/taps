from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class IdeaMatrix(models.Model):
    _name = 'hr.idea.matrix'
    _description = 'Idea Matrix'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char(string="Action Name", required=True, index=True, translate=True)
    sequence = fields.Integer()
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    next_user = fields.Many2many('res.users', ondelete='restrict', string="Next User", index=True, tracking=True)
    description = fields.Text('Content', help='Add content description here...')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The name of the Action Name must be unique per Action Name in company!'),]    
      

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        self.ensure_one()
        default = dict(default or {})
        if 'name' not in default:
            default['name'] = _("%s (copy)") % (self.name)
        return super(IdeaMatrix, self).copy(default=default)