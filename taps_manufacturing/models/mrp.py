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

SIZE_BACK_ORDER_NUMERING = 3


class MrpProduction(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.production'
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    workcenter_id = fields.Many2one('mrp.workcenter', string='Work Center', store=True, readonly=True)

    
    def action_split(self):
        raise UserError(('ggrf'))
    
    def _create_workorder(self):
        for production in self:
            if not production.bom_id:
                continue
            workorders_values = []

            product_qty = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
            exploded_boms, dummy = production.bom_id.explode(production.product_id, product_qty / production.bom_id.product_qty, picking_type=production.bom_id.picking_type_id)

            for bom, bom_data in exploded_boms:
                # If the operations of the parent BoM and phantom BoM are the same, don't recreate work orders.
                if not (bom.operation_ids and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.operation_ids != bom.operation_ids)):
                    continue
                for operation in bom.operation_ids:
                    workorders_values += [{
                        'name': operation.name,
                        'production_id': production.id,
                        'workcenter_id': operation.workcenter_id.id,
                        'product_uom_id': production.product_uom_id.id,
                        'operation_id': operation.id,
                        'state': 'pending',
                        'consumption': production.consumption,
                        'oa_id': production.oa_id.id,
                        'sale_order_line': production.sale_order_line.id,
                    }]
            production.workorder_ids = [(5, 0)] + [(0, 0, value) for value in workorders_values]
            for workorder in production.workorder_ids:
                workorder.duration_expected = workorder._get_duration_expected()
    
    
    
class MrpWorkorder(models.Model):
    """ Manufacturing Orders """
    _inherit = 'mrp.workorder'
    
    oa_id = fields.Many2one('sale.order', related='production_id.oa_id', string='OA', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', related='production_id.sale_order_line', string='Sale Order Line', store=True, readonly=True)
    
    daily_qty_produced = fields.Float(
        'Quantity Produced', default=0.0,
        digits='Product Unit of Measure', compute="_compute_daily_produced",
        copy=False)
    
    @api.depends('time_ids.qty_produced', 'daily_qty_produced')
    def _compute_daily_produced(self):
        for order in self:
            order.daily_qty_produced = sum(order.time_ids.mapped('qty_produced'))
        
    
class MrpWoProductivity(models.Model):
    _inherit = "mrp.workcenter.productivity"
    
    
    qty_produced = fields.Float(
        'Quantity Produced', default=0.0,
        digits='Product Unit of Measure',
        copy=False)