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
    
    total_packed = fields.Integer(string='Total Packed (OA) ',readonly = False, help='Total Packed in this OA')
    total_packed_date = fields.Integer(string='Total Packed (Date) ',readonly = False, help='Total Packed in current Date')
    # compute='_compute_total_packed_date',
    Shade_wise_packed = fields.Integer(string='Total Packed (Shade)',readonly = False, help='Shade wise packed in Current Date') 
    Size_wise_packed = fields.Integer(string='Total Packed(Size)', compute='_compute_total_size_wise_packed', readonly = False, help='Size wise packed in Current Date')


    # @api.depends('lookup_oa')
    # def _compute_total_packed(self):
    #     for rec in self:
    #         total_packed = 0
    #         if rec.lookup_oa:
    #             operations = self.env['operation.details'].sudo().search([
    #                 ('oa_id', '=', rec.lookup_oa.name),
    #                 ('next_operation', '=', 'FG Packing')
    #             ])
    #             total_packed = sum(operations.mapped('qty'))
    #         rec.total_packed = total_packed

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
                    
                unique_dates = set(record.action_date.date() for record in operations)
                all_dates = self.env['selection.fields.data'].sudo().search([('field_name','=','action_date')]).unlink()
                if unique_dates:
                    for _date in unique_dates:
                        self.env["selection.fields.data"].sudo().create({'field_name':'action_date', 'name': _date})
                    self.action_date_list = [(0, 0, {'field_name': 'action_date', 'name': _date}) for _date in unique_dates]
                    
            self.lookup_oa = oa_id
            self.action_date_list = action_date
            self.total_packed = total_packed
        # self.total_packed = total_packed

    @api.depends('Size_list')
    def _compute_total_size_wise_packed(self):
        for rec in self:
            total_packed_date = 0
            shade_list = None

            if rec.action_date_list and rec.lookup_oa:
                date_format = "%Y-%m-%d"
                _date = datetime.strptime(rec.action_date_list.name, date_format)

                operations = self.env['operation.details'].sudo().search([
                    ('oa_id', '=', rec.lookup_oa.id),
                    ('next_operation', '=', 'FG Packing'),
                    ('shade', '=', self.Shade_list.name),
                    
                    ('action_date', '=', _date.date())
                ])

                Size_wise_packed = sum(operations.mapped('qty'))
                rec.Size_wise_packed = Size_wise_packed



    
    @api.onchange('action_date_list')
    def _dates(self):
        oa_id = self.lookup_oa
        action_date = None
        total_packed = self.total_packed
        action_date_list = None
        total_packed_date = None
        shade_list = None  # Initialize shade_list here
        
        if self.action_date_list:
            action_date = self.action_date_list
            date_format = "%Y-%m-%d"
            _date = datetime.strptime(self.action_date_list.name, date_format)
        
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.lookup_oa.id),
                ('next_operation', '=', 'FG Packing')
            ])
        
            operations = operations.filtered(lambda mo: mo.action_date.date() == _date.date())
            if operations:
                total_packed_date = sum(operations.mapped('qty'))
        
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
                self.Shade_list = [(0, 0, {'field_name': 'shade', 'name': _date}) for _shade in unique_shade]
                    # self.update({'Shade_list': [(4, shade_cr.id)]})  # Update the Many2one field
                    # shade_list = shade_cr.id  # Assign value to shade_list
        
            self.lookup_oa = oa_id
            self.action_date_list = action_date
            self.total_packed = total_packed
            self.total_packed_date = total_packed_date
            self.Shade_list = shade_list  # Include shade_list in the final assignment



    @api.onchange('Shade_list', 'action_date_list')
    def _shade_list(self):  
        oa_id = self.lookup_oa
        action_date = None
        total_packed = self.total_packed 
        total_packed_date = self.total_packed_date 
        Shade_list = self.Shade_list
        action_date_list = self.action_date_list
        Shade_wise_packed = None
        if self.Shade_list and self.action_date_list:
            date_format = "%Y-%m-%d"
            _date = datetime.strptime(self.action_date_list.name, date_format)
    
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.lookup_oa.id),
                ('shade', '=', self.Shade_list.name),
                ('next_operation', '=', 'FG Packing'),
            ])
            operations = operations.filtered(lambda mo: mo.action_date.date() == _date.date())
            
            if operations:
                Shade_wise_packed = sum(operations.mapped('qty'))
                # raise UserError(())
    
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
            else:
                # Reset Shade_wise_packed if no matching operations found
                self.Shade_wise_packed = 0
        self.lookup_oa = oa_id
        self.action_date_list = action_date
        self.total_packed = total_packed
        self.total_packed_date = total_packed_date
        self.Shade_wise_packed = Shade_wise_packed
        self.Shade_list = Shade_list 
        self.action_date_list = action_date_list
                    