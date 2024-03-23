import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import _, api, fields, models
import math

class change_production_date(models.TransientModel):
    _name = 'change.production_date'
    _description = 'Change Production Date'
    _check_company_auto = True
    
    oa_id = fields.Char(string='OA', readonly=True)
    from_date = fields.Date(string='From Date')
    production_date = fields.Datetime(string='Production Date', required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        production = self.env["operation.details"].browse(active_id)
        res["from_date"] = production[0].action_date.date()
        return res 
            
    def done_production_date(self):
        if self.from_date == self.production_date.date():
            raise UserError(('You can not Change date to same date'))
            # or advance 
            return
        mo_id = self.env.context.get("active_ids")
        production = self.env["operation.details"].browse(mo_id)
        mrp_data = self.env["manufacturing.order"].search([('oa_id','in',production.oa_id.ids),('closing_date','!=',False)])#browse(mrp_lines)
        
        oa_list = mrp_data.mapped('oa_id')
        
        change_date = production.update({'action_date': self.production_date})
        for oa in oa_list:
            # raise UserError((oa.id))
            last_packing = self.env["operation.details"].search([('next_operation','=','FG Packing'),('oa_id','=',oa.id)]).sorted(key=lambda pr: pr.action_date, reverse=True)[:1]
            change_closing = mrp_data.filtered(lambda pr: pr.oa_id.id == oa.id)
            change_cl_date = change_closing.update({'closing_date': last_packing.action_date})
            sl_closing_date = self.env["sale.order"].browse(oa.id).update({'closing_date': last_packing.action_date})
        
        return
