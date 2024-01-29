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

    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    lookup_oa = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)
    action_date_list = fields.Many2one('selection.fields.data', string='Dates',  domain="[('field_name', '=', 'Dates')]", check_company=True)
    Shade_list = fields.Many2one('selection.fields.data', string='Shade List',  domain="[('field_name', '=', 'shade')]", check_company=True)
    Size_list = fields.Many2one('selection.fields.data', string='Size List', domain="[('field_name', '=', 'size')]", check_company=True)
    
    total_packed = fields.Integer(string='Total Packed (OA) ', help='Total Packed in current Date')
    Shade_wise_packed = fields.Integer(string='Total Packed (Shade)', help='Shade wise packed in Current Date') 
    Size_wise_packed = fields.Integer(string='Total Packed(Size)', help='Size wise packed in Current Date')


    @api.onchange('lookup_oa')
    def _oa(self):
        oa_id=None
        if self.lookup_oa:
            oa_id = self.lookup_oa
            operations = self.env['operation.details'].sudo().search([('oa_id','=',self.lookup_oa.id),('next_operation','=','FG Packing')])
                    
            unique_dates = set(record.action_date.date() for record in operations)
            all_dates = self.env['selection.fields.data'].sudo().search([('field_name','=','Dates')]).unlink()
            if unique_dates:
                for _date in unique_dates:
                    self.env["selection.fields.data"].sudo().create({'field_name':'Dates', 'name': _date})
                self.action_date_list = [(0, 0, {'field_name': 'Dates', 'name': _date}) for _date in unique_dates]
        self.lookup_oa = oa_id

    @api.onchange('action_date_list')
    def _onchange_action_date(self):
        
        if self.lookup_oa and self.action_date_list:
            oa_id = self.lookup_oa.id
            action_date = self.action_date_list.name

            # Filter shades based on OA and Action Date
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', oa_id),
                ('next_operation', '=', 'FG Packing'),
                ('action_date', '=', action_date),
            ])

            unique_shades = set(record.shade for record in operations)
            all_shades = self.env['selection.fields.data'].sudo().search([('field_name', '=', 'shade')]).unlink()
            if unique_shades:
                for shade in unique_shades:
                    self.env["selection.fields.data"].sudo().create({'field_name': 'shade', 'name': shade})

                # Assuming the field name is 'Shade_list', update accordingly
                self.update({'Shade_list': [(5, 0, 0)]})
            self.lookup_oa = oa_id
            self.action_date_list = [(0, 0, {'field_name': 'Dates', 'name': action_date})]
            
    @api.onchange('Shade_list')
    def _onchange_shade(self):
        if self.lookup_oa and self.action_date_list and self.Shade_list:
            oa_id = self.lookup_oa.id
            action_date = self.action_date_list.name
            selected_shade = self.Shade_list.name
    
            # Filter sizes based on OA, Action Date, and Shade
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', oa_id),
                ('next_operation', '=', 'FG Packing'),
                ('action_date', '=', action_date),
                ('shade', '=', selected_shade),
            ])
    
            unique_sizes = set(record.sizcommon for record in operations)
            all_sizes = self.env['selection.fields.data'].sudo().search([('field_name', '=', 'size')]).unlink()
            if unique_sizes:
                for size in unique_sizes:
                    self.env["selection.fields.data"].sudo().create({'field_name': 'size', 'name': size})
    
                # Assuming the field name is 'Size_list', update accordingly
                self.update({'Size_list': [(5, 0, 0)]})
    
            # Use self to set the values of the fields
            # self.lookup_oa = oa_id
            # self.action_date_list = [(0, 0, {'field_name': 'Dates', 'name': action_date})]
            # self.Shade_list = [(0, 0, {'field_name': 'shade', 'name': selected_shade})]
