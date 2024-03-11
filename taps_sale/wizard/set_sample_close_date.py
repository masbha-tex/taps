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

class SetSampleCloseDate(models.TransientModel):
    _name = 'set.sample.cd'
    _description = 'Set Sample Close Date'
    _check_company_auto = True
    
    oa_id = fields.Text(string='OA', readonly=True, required=True)
    oa_count = fields.Integer(string='Number of OA', default=0)
    sample_closed_date = fields.Date(string='Sample Closing Date')
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_ids = self.env.context.get("active_ids")
        mrp = self.env["sale.order"].browse(active_ids)
        oa_ids = mrp.mapped('oa_id.name')
        list_oa_ids = ','.join([i for i in oa_ids])
        
        res["oa_id"] = list_oa_ids
        res["oa_count"] = len(oa_ids)
        return res 
            
    def done_sample_cd(self):
        mo_id = self.env.context.get("active_ids")
        mrp = self.env["sale.order"].browse(mo_id)
        mrp_oa = mrp.update({'closing_date':self.Sample_Closed_Date})
        return
