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

class SetExpectedCloseDate(models.TransientModel):
    _name = 'set.exp.cd'
    _description = 'Set Expected Close Date'
    _check_company_auto = True
    
    oa_id = fields.Text(string='OA', readonly=True, required=True)
    oa_count = fields.Integer(string='Number of OA', default=0)
    exp_close_date = fields.Date(string='Expected Closing Date')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        mrp = self.env["manufacturing.order"].browse(active_ids)
        oa_ids = mrp.mapped('oa_id.name')
        list_oa_ids = ','.join([i for i in oa_ids])
        
        res["oa_id"] = list_oa_ids
        res["oa_count"] = len(oa_ids)
        return res 
            
    def done_exp_cd(self):
        mo_id = self.env.context.get("active_ids")
        mrp = self.env["manufacturing.order"].browse(mo_id)
        mrp_oa = self.env["manufacturing.order"].search([('oa_id', 'in', mrp.oa_id.ids)]).update({'exp_close_date':self.exp_close_date})
        sale_order = self.env["sale.order"].search([('id', 'in', mrp.oa_id.ids)]).update({'exp_close_date':self.exp_close_date})
        # production = mrp_oa.update({'exp_close_date':self.exp_close_date})
        # saleorder = sale_order.update({'exp_close_date':self.exp_close_date})
        return
