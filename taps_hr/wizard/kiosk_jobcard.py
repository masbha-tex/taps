import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import api, fields, models
import math


class StockForecastReport(models.TransientModel):
    _name = 'kiosk.jobcard'
    _description = 'Job Card'
    
    empID = fields.Char('')