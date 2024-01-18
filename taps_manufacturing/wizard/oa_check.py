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

    # lookup_oa = fields.Integer(string='OA No.', help='OA')
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    lookup_oa = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)
    action_date_list = fields.Many2one('selection.fields.data', string='Dates',  domain="[('field_name', '=', 'Dates')]", check_company=True)
    iteam = fields.Integer(string='Iteam', help='Iteam')
    Shade_list = fields.Integer(string='Shade List', help='Shade List')
    Size_list = fields.Integer(string='Size List', help='OA')
    
    total_packed = fields.Integer(string='Total Packed (OA) ', help='Total Packed in current Date')
    Shade_wise_packed = fields.Integer(string='Total Packed (Shade)', help='Shade wise packed in Current Date') 
    Size_wise_packed = fields.Integer(string='Total Packed(Size)', help='Size wise packed in Current Date')


    @api.onchange('lookup_oa')
    def _oa(self):
        if self.lookup_oa:
            operations = self.env['operation.details'].sudo().search([('oa_id','=',self.lookup_oa.id),('next_operation','=','FG Packing')])
            unique_dates = set(record.action_date.date() for record in operations)
            all_dates = self.env['selection.fields.data'].sudo().search([('field_name','=','Dates')]).unlink()
            if unique_dates:
                for _date in unique_dates:
                    self.env["selection.fields.data"].sudo().create({'field_name':'Dates',
                                                                              'name':_date
                                                                              })
                self.action_date_list = [(0, 0, {'field_name': 'Dates', 'name': _date}) for _date in unique_dates]


