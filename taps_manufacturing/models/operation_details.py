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


class OperationDetails(models.Model):
    _name = "operation.details"
    _description = "Operation Details"
    _check_company_auto = True

    code = fields.Text(string='Code', store=True)
    mrp_lines = fields.Char(string='Mrp lines', store=True)
    sale_lines = fields.Char(string='Sale lines', store=True)
    
    mrp_line = fields.Many2one('manufacturing.order', string='Mrp Id', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', store=True, readonly=True)
    operation_of = fields.Selection([
        ('plan', 'Planning'),
        ('lot', 'Create Lot'),
        ('output', 'Output'),
        ('req', 'Requisition')],
        string='Operation Of')
    operation_by = fields.Text(string='Operation By', store=True)
    based_on = fields.Text(string='Based On', store=True)
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0 readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=True, compute='get_balance')

    def get_balance(self):
        for s in self:
            s.balance_qty = s.qty - s.done_qty







