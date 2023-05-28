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
_logger = logging.getLogger(__name__)



class SplitManufacturingOrder(models.TransientModel):
    _name = 'mrp.split'
    _description = 'Split Manufacturing Order'
    _check_company_auto = True
    
    mo_id = fields.Many2one('mrp.production', 'Manufacturing Order', readonly=True)
    mo_qty = fields.Float(
        'Total Qty',digits='Product Unit of Measure',
        readonly=True)#,states={'draft': [('readonly', False)]}
    split_line = fields.One2many('mrp.split.line', 'split_id', string='Split Lines',copy=True, auto_join=True)
    split_totalqty = fields.Float(string='Total', store=True, readonly=True, compute='_qty_all')
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    
    @api.depends('split_line.qty_total')
    def _qty_all(self):
        """
        Compute the total amounts of the SO.
        """
        for split in self:
            qty = 0.0
            for line in split.split_line:
                qty += line.qty_total
            split.update({
                'split_totalqty': qty,
            })    
            
    
    def done_mo_split(self):
        a = ''
                
            
    
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
    qty_total = fields.Float(compute='_compute_amount', string='Total', readonly=True, store=True)    
    company_id = fields.Many2one(related='split_id.company_id', string='Company', store=True, readonly=True, index=True)
    
    @api.depends('product_qty')
    def _compute_qty(self):
        """
        Compute the amounts of the SO line.
        """
        qty = 0
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            qty += line.product_qty
            line.update({'qty_total': qty})    