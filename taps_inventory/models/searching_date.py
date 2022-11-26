from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class Inventory(models.Model):
    _name = "searching.date"
    _description = "Search By Date"
    
    
    from_date = fields.Datetime('From',readonly=True)
    to_date = fields.Datetime('To',readonly=True)