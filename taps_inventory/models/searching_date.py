from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class Inventory(models.Model):
    _name = "searching.date"
    _auto = False
    _description = "Search By Date"