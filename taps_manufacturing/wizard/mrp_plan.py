import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import _, api, fields, models
import math

from typing import List, Union

_logger = logging.getLogger(__name__)


class ManufacturingPlan(models.TransientModel):
    _name = 'mrp.plan'
    _description = 'Manufacturing Plan'
    _check_company_auto = True

    plan_for = fields.Selection([
        ('dyeing', 'Dyeing'),
        ('sliderplating', 'Slider Plating'),
        ('topplating', 'Top Plating'),
        ('bottomplating', 'Bottom Plating')],
        string='Plan For')
    
    plan_start = fields.Datetime(string='Start Date', required=True)
    plan_end = fields.Datetime(string='End Date', required=True)
    item_qty = fields.Float('Item Qty',digits='Product Unit of Measure', readonly=True)
    material_qty = fields.Float('Material Qty',digits='Product Unit of Measure', readonly=True)
    plan_qty = fields.Float(string='Qty', store=True, compute='_qty_all', default=1.0, digits='Product Unit of Measure')
    
    def done_mo_plan(self):
        if self.split_totalqty > self.mo_qty:
            raise UserError(('Split quantity should not greterthen the base quantity'))
            return
        return self.mo_id.split_mo(self.mo_id.id,self.split_line)