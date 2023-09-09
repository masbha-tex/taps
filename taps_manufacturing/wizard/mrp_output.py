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


class ManufacturingOutput(models.TransientModel):
    _name = 'mrp.output'
    _description = 'Process Output'
    _check_company_auto = True
    
    lot_code = fields.Char(string='Lot', readonly=False)
    # enter_pressed = fields.Boolean(string='Enter Pressed', default=False)
    oa_id = fields.Many2one('sale.order', string='OA', readonly=True)
    item = fields.Text(string='Item', readonly=True)
    shade = fields.Text(string='Shade', readonly=True)
    finish = fields.Text(string='Finish', readonly=True) 
    sizein = fields.Text(string='Size (Inc)', readonly=True)
    sizecm = fields.Text(string='Size (Cm)', readonly=True)
    output_of = fields.Text(string='Production Of', readonly=True)
    manuf_date = fields.Datetime(string='Production Date', required=True, default=datetime.now())
    planned_qty = fields.Float(string='Planned Qty', digits='Product Unit of Measure', readonly=True)
    qty = fields.Float(string='Qty', default=0.0, digits='Product Unit of Measure',required=True)
    
    # @api.model
    # def default_get(self, fields_list):
    #     res = super().default_get(fields_list)
    #     active_model = self.env.context.get("active_model")
    #     active_id = self.env.context.get("active_id")
    #     production = self.env["operation.details"].browse(active_id)
    #     res["lot_code"] = production[0].code
    #     res["oa_id"] = production[0].oa_id.id
    #     res["item"] = production[0].fg_categ_type
    #     res["shade"] = production[0].shade
    #     res["finish"] = production[0].finish
    #     # res["sizein"] = production[0].size_in
    #     # res["sizecm"] = production[0].size_cm
    #     res["output_of"] = production[0].work_center.name
    #     return res 
            
    def done_mo_output(self):
        # mo_ids = self.env.context.get("active_ids")
        # active_model = self.env.context.get("active_model")
        # production = self.env[""+active_model+""].browse(mo_ids)
        production = self.env['operation.details'].search([('name', '=', self.lot_code),('name', '!=', None)])
        mo_ids = production.mapped('id')
        production.set_output(self._name,mo_ids,self.manuf_date,self.qty,self.output_of)
        #production.set_operation(mo_ids,self.plan_for,self.machine_line)
        return
    
    @api.model
    def onevent_lot(self,code=None):
        self.lot_code = ''
        self.lot_code = code
        # production = self.env['operation.details'].search([('code', '=', code),('code', '!=', None)])
        # #raise UserError((production[0].oa_id.id))
        # values = [production[0].oa_id.id,production[0].fg_categ_type,production[0].shade,production[0].finish,
        #           production[0].work_center.name]
        return code

        # if production:
        #     self.lot_code = production[0].code
        #     self.oa_id = production[0].oa_id.id
        #     self.item = production[0].fg_categ_type
        #     self.shade = production[0].shade
        #     self.finish = production[0].finish
        #     self.output_of = production[0].work_center.name    

    @api.model
    def get_production_details(self, code=None):
        production = self.env['operation.details'].search([('name', '=', code), ('name', '!=', None)])
        values = {}
        if production:
            values['lot_code'] = production[0].name
            values['oa_id'] = production[0].oa_id.id
            values['item'] = production[0].fg_categ_type
            values['shade'] = production[0].shade
            values['finish'] = production[0].finish
            values['output_of'] = production[0].work_center.name
            values['planned_qty'] = production[0].qty
        return values



    
    @api.onchange('lot_code')
    def _on_lot_code_change(self):
        production = self.env['operation.details'].search([('name', '=', self.lot_code),('name', '!=', None),('next_operation', 'like', 'Output')])
        if production:
            self.lot_code = production[0].name
            self.oa_id = production[0].oa_id.id
            self.item = production[0].fg_categ_type
            self.shade = production[0].shade
            self.finish = production[0].finish
            self.sizein = production[0].sizein
            self.sizecm = production[0].sizecm
            # res["sizein"] = production[0].size_in
            # res["sizecm"] = production[0].size_cm
            self.output_of = production[0].work_center.name
            self.planned_qty = production[0].qty
        else:
            if self.lot_code:
                return {'warning': {'title': 'Warning', 'message': 'This lot is not for output'}}
