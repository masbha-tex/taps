from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class Title(models.Model):
    _name = 'hs.title'
    _description = 'Health & Safety Title'
    _inherit = ['mail.thread']
    _rec_name = 'name'

    name = fields.Char(string="Title", required=True, index=True, translate=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    criteria_id = fields.Many2one('hs.criteria', string='Title')
    description = fields.Text('Content', help='Add content description here...')

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id, criteria_id)', 'The name of the hs title must be unique per hs criteria in company!'),]    

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
        return super(Title, self).copy(default=default)