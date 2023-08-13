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


class SplitManufacturingOrder(models.TransientModel):
    _name = 'mrp.split'
    _description = 'Split Manufacturing Order'
    _check_company_auto = True
    
    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order', readonly=True, ondelete="cascade")
    product_id = fields.Many2one('product.product', 'Product', readonly=True, required=True, check_company=True)
    
    mo_qty = fields.Float('Total Qty',digits='Product Unit of Measure', readonly=True)
    #,states={'draft': [('readonly', False)]}
    split_line = fields.One2many('mrp.split.line', 'split_id', string='Split Lines',copy=True, auto_join=True)
    split_totalqty = fields.Float(string='Total', store=True, compute='_qty_all', default=1.0, digits='Product Unit of Measure')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    
    @api.depends('split_line.qty_total')
    def _qty_all(self):
        """
        Compute the total splited.
        """
        for split in self:
            qty = 0.0
            for line in split.split_line:
                qty += line.qty_total
            split.update({
                'split_totalqty': qty
            })
            
    
    def done_mo_split(self):
        if self.split_totalqty > self.mo_qty:
            raise UserError(('Split quantity should not greterthen the base quantity'))
            return
        return self.mo_id.split_mo(self.mo_id.id,self.split_line)#with_context({'disable_cancel_warning': True}).
                
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        # Auto-complete production_id from context
        #if "mo_id" in fields_list and active_model == "mrp.production":
        res["mo_id"] = active_id
        production = self.env["mrp.production"].browse(active_id)
        res["mo_qty"] = production.product_qty
        res["product_id"] = production.product_id.id
            #raise UserError((active_id))
            #if production.product_tracking == "serial":
                
        # # Auto-complete split_qty from production_id
        # if "split_qty" in fields_list and res.get("production_id"):
        #     production = self.env["mrp.production"].browse(res["production_id"])
        #     res["split_qty"] = production._get_quantity_to_backorder()
        return res            
    
class SplitManufacturingOrderLine(models.TransientModel):
    _name = 'mrp.split.line'
    _description = 'Split Manufacturing Order'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True
    
    sequence = fields.Integer(string='Sequence', default=10)
    split_id = fields.Many2one('mrp.split', string='Split MO', required=True, ondelete='cascade', index=True, copy=False)    
    product_qty = fields.Float('Quantity To Produce',default=1.0, digits='Product Unit of Measure',required=True)
    
    #,states={'draft': [('readonly', False)]}
    date_planned_start = fields.Datetime(
        'Scheduled Date', copy=False, 
        # default=_get_default_date_planned_start,
        help="Date at which you plan to start the production.",
        index=True, required=True)
    
    date_planned_finished = fields.Datetime(
        'Scheduled End Date',
        # default=_get_default_date_planned_finished,
        help="Date at which you plan to finish the production.",
        copy=False)
    qty_total = fields.Float(compute='_compute_qty', string='Total', store=True)    
    company_id = fields.Many2one(related='split_id.company_id', string='Company', store=True, readonly=True, index=True)
    
    @api.depends('product_qty')
    def _compute_qty(self):
        """
        Compute the quantity of the Split line.
        """
        qty = 0
        for line in self:
            qty += line.product_qty
            line.update({'qty_total': qty})
            
            
    # @api.onchange('product_qty')
    # def product_qty_change(self):
    #     qty = 0
    #     for line in self:
    #         qty += line.product_qty
    #         line.update({'qty_total': qty})



