import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
import re
import math



class OaCheck(models.TransientModel):
    _name = 'oa.check'
    _description = 'OA Check'     


    lookup_oa = fields.Integer(string='OA No.', help='OA')
    # action_date_list = fields.Integer(string='Packing Date', help='Packing Date')
    action_date_list = fields.Selection(
        selection=[],
        string="Packing Date",
    )
    iteam = fields.Integer(string='Iteam', help='Iteam')
    Shade_list = fields.Integer(string='Shade List', help='Shade List')
    Size_list = fields.Integer(string='Size List', help='OA')
    
    total_packed = fields.Integer(string='Total Packed (OA) ', help='Total Packed in current Date')
    Shade_wise_packed = fields.Integer(string='Total Packed (Shade)', help='Shade wise packed in Current Date')
    Size_wise_packed = fields.Integer(string='Total Packed(Size)', help='Size wise packed in Current Date')



    @api.onchange('lookup_oa')
    def _oa(self):
        if self.lookup_oa:
            oa_data = self.env["operation.details"].search([('oa_id.name','ilike',self.lookup_oa),('next_operation','=','FG Packing')])
            unique_dates = set(record.action_date.date() for record in oa_data)
            sorted_dates = sorted(unique_dates)
            # selection_data = []
            selection_data = [('%s' % str(date), '%s' % str(date)) for date in sorted_dates]
            # raise UserError((selection_data))
            self.action_date_list = selection_data
    

    # @api.onchange('lookup_oa')
    # def _oa(self):
    #     if self.lookup_oa:
    #         oa_data = self.env["operation.details"].search([('oa_id.name','ilike',self.lookup_oa),('next_operation','=','FG Packing')])
    #         # oa_date_list = oa_data.mapped('action_date')
    #         unique_dates = set(record.action_date.date() for record in oa_data)

    #         sorted_dates = sorted(unique_dates)
    #         selection_data = [(str(date), str(date)) for date in sorted_dates]
            
    #         # selection_data = [(str(date), str(date)) for date  in unique_dates]
            
    #         # raise UserError((selection_data))
    #         self.action_date_list = selection_data



    
   