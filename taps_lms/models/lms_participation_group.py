from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class ParticipationGroup(models.Model):
    _name = 'lms.participation.group'
    _description = 'Participation Group'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    name = fields.Char('Participation Group', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Training Participation Group must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

