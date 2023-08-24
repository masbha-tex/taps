from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class SessionVenue(models.Model):
    _name = 'lms.session.venue'
    _description = 'Session Venue'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    name = fields.Char('Session Venue', required=True)
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', string='Company')
    color = fields.Integer('Color Index')

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Training Session Venue must be unique!'),]      
 

