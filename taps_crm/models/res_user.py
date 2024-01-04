from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    active_date = fields.Date(string="Activation Date")