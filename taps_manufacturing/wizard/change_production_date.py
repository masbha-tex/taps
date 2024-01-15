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
        active_id = self.env.context.get("active_id")
        production = self.env["operation.details"].browse(active_id)
        res["from_date"] = production[0].action_date.date()
        return res 
            
    def done_production_date(self):
        if self.from_date <= self.production_date.date():
            raise UserError(('You can not Change date to same or advance date'))
            return
        mo_id = self.env.context.get("active_id")
        production = self.env["operation.details"].browse(mo_id)
        
        mrp_data = self.env["manufacturing.order"].search([('oa_id','in',production.oa_id.ids)])#browse(mrp_lines)
        
        change_date = production.update({'action_date': self.production_date})
        # mrp_to_close = mrp_data.filtered(lambda pr: pr.closing_date.date() == production[0].action_date.date())
        # if mrp_to_close:
        #     change_closing_date = mrp_to_close.update({'closing_date': self.production_date})
        #     sale_order = self.env["sale.order"].browse(change_closing_date.oa_id.ids)
        #     change_sale_order_closing_date = sale_order.update({'closing_date': change_closing_date[0].closing_date})
        
        return
