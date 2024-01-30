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
    action_date_list = fields.Many2one('selection.fields.data',string='Dates',  domain="[('field_name', '=', 'action_date')]", check_company=True)
    Shade_list = fields.Many2one('selection.fields.data', string='Shade List',  domain="[('field_name', '=', 'shade')]", check_company=True)
    Size_list = fields.Many2one('selection.fields.data', string='Size List', domain="[('field_name', '=', 'size')]", check_company=True)
    
    total_packed = fields.Integer(string='Total Packed (OA) ', help='Total Packed in this OA')
    total_packed_date = fields.Integer(string='Total Packed (Date) ', help='Total Packed in current Date')
    Shade_wise_packed = fields.Integer(string='Total Packed (Shade)', help='Shade wise packed in Current Date') 
    Size_wise_packed = fields.Integer(string='Total Packed(Size)', help='Size wise packed in Current Date')


    @api.onchange('lookup_oa')
    def _oa(self):
        oa_id= None
        action_date = None
        total_packed = None
        if self.lookup_oa:
            oa_id = self.lookup_oa
            operations = self.env['operation.details'].sudo().search([
                ('oa_id','=',self.lookup_oa.id), ('next_operation','=','FG Packing')])
            if operations:
                total_packed = sum(operations.mapped('qty'))
                # raise UserError(qty)  
                self.total_packed = total_packed
            else:
                # Clear Qty field if no operations are found
                self.total_packed = 0
                    
            unique_dates = set(record.action_date.date() for record in operations)
            all_dates = self.env['selection.fields.data'].sudo().search([('field_name','=','action_date')]).unlink()
            if unique_dates:
                for _date in unique_dates:
                    self.env["selection.fields.data"].sudo().create({'field_name':'action_date', 'name': _date})
                self.action_date_list = [(0, 0, {'field_name': 'action_date', 'name': _date}) for _date in unique_dates]
                
        self.lookup_oa = oa_id
        # self.action_date_list = action_date
        self.total_packed = total_packed
        
    @api.onchange('action_date_list')
    def _dates(self):
        oa_id = None
        action_date = None
        total_packed = None
        action_date_list = None
        total_packed_date = None
        shade_list = None
    
        if self.action_date_list:
            date_format = "%Y-%m-%d"
            _date = datetime.strptime(self.action_date_list.name, date_format)
    
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.lookup_oa.id),
                ('next_operation', '=', 'FG Packing')])
    
            operations = operations.filtered(lambda mo: mo.action_date.date() == _date.date())
            if operations:
                self.total_packed_date = sum(operations.mapped('qty'))
    
                # Shade list
                unique_shade = set(record.shade for record in operations)
                shade_records = self.env['selection.fields.data'].sudo().search([
                    ('field_name', '=', 'shade')
                ])
                shade_records.unlink()  # Remove existing records
    
                for _shade in unique_shade:
                    shade_cr = self.env["selection.fields.data"].sudo().create({
                        'field_name': 'shade',
                        'name': _shade
                    })
                    self.update({'Shade_list': [(4, shade_cr.id)]})  # Update the Many2one field
                    shade_list = shade_cr.id
    
        self.lookup_oa = oa_id
        self.action_date_list = action_date
        self.total_packed = total_packed
        # self.total_packed_date = total_packed_date
        # self.Shade_list = shade_list

        @api.onchange('Shade_list')
        def _shade_list(self):
            oa_id = None
            if self.action_date_list:
                date_format = "%Y-%m-%d"
                _date = datetime.strptime(self.action_date_list.name, date_format)
    
                operations = self.env['operation.details'].sudo().search([
                    ('oa_id', '=', self.lookup_oa.id),
                    ('shade', '=', self.Shade_list),
                    ('next_operation', '=', 'FG Packing'),
                    ('action_date', '=', _date.date())
                ])
    
                if operations:
                    self.Shade_wise_packed = sum(operations.mapped('qty'))
    
                    # Size list
                    unique_size = set(record.sizcommon for record in operations)
                    size_records = self.env['selection.fields.data'].sudo().search([
                        ('field_name', '=', 'size')
                    ])
                    size_records.unlink()  # Remove existing records
    
                    for _size in unique_size:
                        size_cr = self.env["selection.fields.data"].sudo().create({
                            'field_name': 'size',
                            'name': _size
                        })
                        self.update({'Size_list': [(4, size_cr.id)]})  # Update the Many2one field
                        
        self.lookup_oa = oa_id


                