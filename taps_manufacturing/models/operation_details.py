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

    code = fields.Char(string='Code', store=True)
    mrp_lines = fields.Char(string='Mrp lines', store=True)
    sale_lines = fields.Char(string='Sale lines', store=True)
    
    mrp_line = fields.Many2one('manufacturing.order', string='Mrp Id', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)

    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    action_date = fields.Datetime(string='Action Date', readonly=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    #buyer_name = fields.Many2one('sale.buyer', related='oa_id.buyer_name', string='Buyer', readonly=True)
    
    slidercodesfg = fields.Char(string='Slider Code (SFG)', store=True, readonly=True)
    finish = fields.Char(string='Finish', store=True, readonly=True)
    shade = fields.Char(string='Shade', store=True, readonly=True)

    
    operation_of = fields.Selection([
        ('plan', 'Planning'),
        ('lot', 'Create Lot'),
        ('output', 'Output'),
        ('req', 'Requisition')],
        string='Operation Of')
    operation_by = fields.Text(string='Operation By', store=True)
    based_on = fields.Char(string='Based On', store=True)
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=True, compute='get_balance')
    num_of_lots = fields.Integer(string='N. of Lots', readonly=True, compute='get_lots')
 
    def get_balance(self):
        for s in self:
            s.balance_qty = s.qty - s.done_qty
    
    def get_lots(self):
        for s in self:
            s.num_of_lots = 1
            
    def button_requisition(self):
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_requisition")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action
  
    def button_output(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

    def button_start(self):#button_createlot
        self.ensure_one()
        



