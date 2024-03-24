from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from random import randint


class BusinessExcellenceImpact(models.Model):
    _name = 'business.excellence.impact'
    _description = 'Business Excellence Area Impact'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    # name = fields.Char('Area Imapct', required=True)
    
    # company_id = fields.Many2one('res.company', string='Company')
    # title_ids = fields.One2many('business.excellence.title', 'criteria_id', string='Scope')
    # color = fields.Integer('Color Index')
    
    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Area Imapct', required=True, translate=True)
    active = fields.Boolean('Active', default=True)
    color = fields.Integer('Color', default=_get_default_color)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Business Excellence area impact must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

