from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class FgCategory(models.Model):
    _name = "fg.category"
    _description = "Finish Goods Categories"

    name = fields.Char(string='Category', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)
    active = fields.Boolean('Active', default = True)