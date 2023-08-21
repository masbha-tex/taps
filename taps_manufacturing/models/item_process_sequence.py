import json
import datetime
import math
import operator as py_operator
import re

from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from werkzeug.urls import url_encode

SIZE_BACK_ORDER_NUMERING = 3


class ProcessSequence(models.Model):
    _name = "process.sequence"
    _description = "Sequence of Manufacturing Process"
    _order = 'id asc'
    _check_company_auto = True

    item = fields.Char(string='Item', store=True, readonly=True)
    sequence = fields.Integer(string='Sequence', store=True, readonly=True)
    process = fields.Char(string='Process', store=True, readonly=True)
    work_center = fields.Many2one('mrp.workcenter', string='Work Center', store=True, readonly=True)

    



