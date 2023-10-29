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


class ManufacturingGroupOutput(models.TransientModel):
    _name = 'mrp.group.output'
    _description = 'Process Output'
    _check_company_auto = True
    
    machine_no = fields.Char(string='Machine', readonly=True)
    oa_id = fields.Char(string='Lot', readonly=True)
    item = fields.Char(string='Item', readonly=True)
    shade = fields.Text(string='Shade', readonly=True)
    # manuf_date = fields.Datetime(string='Production Date', required=True, default=datetime.now())
    planned_qty = fields.Float(string='Dyed Balance Qty', digits='Product Unit of Measure', readonly=True)
    oa_tape_qty = fields.Float(string='OA Tape Balance', digits='Product Unit of Measure', readonly=True)
    qty = fields.Float(string='Qty', default=0.0, digits='Product Unit of Measure',required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        production = self.env["operation.details"].browse(active_id)
        res["machine_no"] = production[0].machine_no.name
        res["oa_id"] = production[0].oa_id.name
        res["item"] = production[0].fg_categ_type
        res["shade"] = production[0].shade
        res["planned_qty"] = sum(production.mapped('balance_qty'))
        res["oa_tape_qty"] = sum(production.mapped('ac_balance_qty'))
        
        # res["planned_qty"] = sum(oa_tape_qty
        return res 
            
    def done_mo_output(self):
        mo_ids = self.env.context.get("active_ids")
        production = self.env["operation.details"].browse(mo_ids)
        production.set_group_output(mo_ids,self.qty)#self.manuf_date,
        return
