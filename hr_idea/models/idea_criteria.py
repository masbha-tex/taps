from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class Criteria(models.Model):
    _name = 'idea.criteria'
    _description = 'Idea Criteria'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    name = fields.Char('Title', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    title_ids = fields.One2many('idea.title', 'criteria_id', string='Scope')
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Reward Criteria must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

