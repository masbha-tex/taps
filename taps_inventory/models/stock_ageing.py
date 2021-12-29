from odoo import models, fields, api
from odoo.tools.misc import format_datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

class taps_inventory(models.Model):
    _inherit = 'stock.move.line'
    _description = 'Stok Ageing'
    
    duration = fields.Integer(string='Duration', compute='_compute_duration', readonly=True)
    #x_studio_schedule_date
    
    @api.depends('product_id', 'x_studio_schedule_date')
    def _compute_duration(self):
        for line in self:
            dur = datetime.now()-line.x_studio_schedule_date
            line.duration = dur.days