from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class Criteria(models.Model):
    _name = 'business.excellence.criteria'
    _description = 'Business Excellence Criteria'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    name = fields.Char('Title', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    title_ids = fields.One2many('business.excellence.title', 'criteria_id', string='Scope')
    color = fields.Integer('Color Index')
    

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Business Excellence must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

