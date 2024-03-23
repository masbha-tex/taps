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
from datetime import datetime

class FgPackaging(models.Model):
    _name = "mis.dashboard"
    _description = "Mis Dashboard"
    _check_company_auto = True

    name = fields.Char(string='Carton')