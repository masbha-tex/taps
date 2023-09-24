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


class MrpDelivery(models.TransientModel):
    _name = 'mrp.delivery'
    _description = 'Delivery Order'
    _check_company_auto = True

    oa_id = fields.Text(string='OA', readonly=True)
    item = fields.Text(string='Item', readonly=True)
    
    total_qty_pcs = fields.Float('Qty in Pcs', digits='Product Unit of Measure', readonly=True)
    total_qty_pack = fields.Float('Qty in Pack', digits='Product Unit of Measure', readonly=True)
    total_weight = fields.Float('Total Weight', digits='Product Unit of Measure')
    deliveri_date = fields.Datetime(string='Delivery Date', required=True, default=datetime.now())
    
    delivery_line = fields.One2many('mrp.delivery.line', 'delivery_id',  string='Delivery List',copy=True, auto_join=True)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        operation = self.env[""+active_model+""].browse(active_id)
        
        orderline_values = []

        for lines in operation:
            orderline_values.append((0, 0, {
                'cartoon': lines.name,
                'shade': lines.shade,
                'finish': lines.finish,
                'slider': lines.slidercodesfg,
                'sizein': lines.sizein,
                'sizecm': lines.sizecm,
                'qty_pcs': lines.qty,
                'qty_pack': lines.pack_qty,
                }))
            
        res.update({'oa_id': operation[0].oa_id.name,
                    'item': operation[0].fg_categ_type,
                    'total_qty_pcs': sum(operation.mapped('qty')),
                    'total_qty_pack': sum(operation.mapped('pack_qty')),
                    'delivery_line': orderline_values,
                    })
        return res
            
    def done_mr_delivery(self):
        active_model = self.env.context.get("active_model")
        ope_id = self.env.context.get("active_ids")
        return self.env['operation.details'].set_delivery_order(active_model,ope_id,self,self.delivery_line)


class MrpDeliveryLine(models.TransientModel):
    _name = 'mrp.delivery.line'
    _description = 'Delivery Details'
    _check_company_auto = True

    delivery_id = fields.Many2one('mrp.delivery', string='Delivery ID', ondelete='cascade', index=True, copy=False)
    cartoon = fields.Char(string='Cartoon', readonly=True)
    shade = fields.Char(string='Shade', readonly=True)
    finish = fields.Char(string='Finish', readonly=True)
    slider = fields.Char(string='Slider', readonly=True)
    sizein = fields.Char(string='Size (Inc)', readonly=True)
    sizecm = fields.Char(string='Size (CM)', readonly=True)

    qty_pcs = fields.Float('Qty in Pcs', digits='Product Unit of Measure', readonly=True)
    qty_pack = fields.Float('Qty in Pack', digits='Product Unit of Measure', readonly=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        res.update({
            'cartoon': '',
            'shade': '',
            'finish': '',
            'slider': '',
            'sizein': '',
            'sizecm': '',
            'qty_pcs': 0.0,
            'qty_pack': 0.0,
        })

        return res