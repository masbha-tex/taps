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


class ManufacturingLot(models.TransientModel):
    _name = 'mrp.lot'
    _description = 'Mrp Lot'
    _check_company_auto = True

    item = fields.Text(string='Item', readonly=True)
    shade_finish = fields.Text(string='Shade / Finish', readonly=True)
    size = fields.Text(string='Size', readonly=True)
    work_center = fields.Many2one('mrp.workcenter', string='Create From', readonly=True)
    
    #item_qty = fields.Float('Item Qty',digits='Product Unit of Measure', readonly=True)
    material_qty = fields.Float('Material Qty',digits='Product Unit of Measure', readonly=True)
    
    lot_line = fields.One2many('lot.line', 'lot_id',  string='Lot List',copy=True, auto_join=True)
    

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        
        operation = self.env[""+active_model+""].browse(active_id)
        res["item"] = operation[0].fg_categ_type
        
        res["shade_finish"] = operation[0].shade + operation[0].finish
        
        #res["size"] = operation[0].size
        if active_model == 'manufacturing.order':
            res["work_center"] = 3
            res["material_qty"] = operation[0].product_uom_qty
            size = operation[0].sizein + ' Inc'
            if operation[0].sizein == 'N/A':
                size = operation[0].sizecm + ' CM'
                
            res["size"] = size
        else:
            res["work_center"] = operation[0].work_center.id
            res["material_qty"] = operation[0].qty
        return res 
            
    def done_mo_lot(self):
        # if  self.plan_qty > self.material_qty:
        #     raise UserError(('Split quantity should not greterthen the base quantity'))
        #     return
        active_model = self.env.context.get("active_model")
        ope_id = self.env.context.get("active_id")
        operation = self.env['operation.details'].browse(1)
        if self.material_qty < sum(self.lot_line.mapped('material_qty')):
            raise UserError(('You can not create lot more order quantity'))
            return self
        else:
            return operation.set_lot(active_model,ope_id,self.lot_line)


class LotLine(models.TransientModel):
    _name = 'lot.line'
    _description = 'Lot Details'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True

    lot_id = fields.Many2one('mrp.lot', string='Lot ID', ondelete='cascade', index=True, copy=False)
    lot_code = fields.Char(string='Lot', store=True)
    material_qty = fields.Float('Quantity', default=0.0, digits='Product Unit of Measure', required=True)
    
    
#     @api.depends('product_qty')
#     def _compute_qty(self):
#         """
#         Compute the quantity of the Split line.
#         """
#         qty = 0
#         for line in self:
#             qty += line.product_qty
#             line.update({'qty_total': qty})
