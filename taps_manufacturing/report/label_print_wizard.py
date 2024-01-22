import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta
import re
import math
import calendar
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
_logger = logging.getLogger(__name__)


class LabelPrintingWizard(models.TransientModel):
    _name = 'label.print'
    _description = 'Label Printing'
    _check_company_auto = True
    
    logo = "https://www.texfasteners.com/wp-content/uploads/2017/08/logo_tex_tiny_2x.png" 
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    report_type = fields.Selection([('pplg', 'Production Packing Label (General)'),('fgcl', 'FG Carton Label'),('pplo', 'Production Packing Label (Others)')], string='Report Type', required=True, help='Report Type', default='pplg')
    
    company_name = fields.Char('Company Name', readonly=False, default='TEX ZIPPERS (BD) LIMITED')     
    company_address = fields.Char('Company Address', readonly=False, default='Plot # 180, 264 & 273 Adamjee Export Processing Zone, Adamjee Nagar, Shiddhirgonj, Narayangonj, Bangladesh')  

    table_name = fields.Selection([('a', 'Table A'),('b', 'Table B')], string='Table', required=True, help='Table', default='a')
    Country_name = fields.Selection([('bangladesh', 'Bangladesh'),('vietnam', 'Vietnam'),('pakistan', 'Pakistan')], string='Country', required=True, help='Country', default='bangladesh')


    oa_number = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)

    iteam = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'Iteams')]", check_company=True, string='Iteam', store=True, required=False, readonly=False)
    shade = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'shade')]", check_company=True, string='Shade', store=True, required=False, readonly=False)
    finish = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'finish')]", check_company=True, string='Finish', store=True, readonly=False)
    size = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'size')]", check_company=True, string='Size', store=True, required=False, readonly=False)
    qty = fields.Integer('Qty', readonly=False, default='')

    batch_lot = fields.Char('Batch/Lot', readonly=False, default='')
    
    qc_person = fields.Many2one('hr.employee', string="QC By", domain="[('active', '=', True), ('department_id', '=', 272)]", index=True, required=True,readonly=False)
    pre_check_person = fields.Many2one('hr.employee', string="Pre Check By", domain="[('active', '=', True), ('department_id', '=', 281)]", index=True, required=True,readonly=False)
    printing_person = fields.Many2one('hr.employee', string="Print By", domain="[('active', '=', True), ('department_id', '=', 284)]", index=True, required=True,readonly=False)

    
    @api.onchange('oa_number')
    def _onchange_oa_number(self):
        oa_id = None
        if self.oa_number:
            oa_id = self.oa_number
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.oa_number.id),
                ('next_operation', '=', 'Packing Output')
            ])
    
            if operations:
                # Iteam List
                unique_iteam = set(record.product_template_id.name for record in operations)
                iteam_records = self.env['selection.fields.data'].sudo().search([
                    ('field_name', '=', 'Iteams')
                ])
                iteam_records.unlink()
    
                for _iteam in unique_iteam:
                    iteam_cr = self.env["selection.fields.data"].sudo().create({
                        'field_name': 'Iteams',
                        'name': _iteam
                    })
                    self.update({'iteam': [(4, iteam_cr.name)]})
                    
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
                    self.update({'shade': [(4, shade_cr.name)]})  # Add the record to the Many2one field
            else:
                # Clear Iteam field if no operations are found
                self.update({'iteam': [(5, 0, 0)]})
                self.update({'shade': [(5, 0, 0)]})
        self.oa_number = oa_id
    
    @api.onchange('shade')
    def _onchange_shade(self):
        oa_id = None
        iteam = None
        shade = None
        if self.shade:
            oa_id = self.oa_number
            iteam = self.iteam
            shade = self.shade
            # raise UserError((self.oa_number.id,self.shade.name))
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.oa_number.id),
                ('shade', '=', self.shade.name), 
                ('next_operation', '=', 'Packing Output')
            ])
    
            if operations:
                # Finish list
                unique_finish = set(record.finish for record in operations)
                finish_records = self.env['selection.fields.data'].sudo().search([
                    ('field_name', '=', 'finish')
                ])
                finish_records.unlink()
    
                for _finish in unique_finish:
                    finish_cr = self.env["selection.fields.data"].sudo().create({
                        'field_name': 'finish',
                        'name': _finish
                    })
                    self.update({'finish': [(4, finish_cr.name)]})
            else:
                # Clear Finish field if no operations are found
                self.update({'finish': [(5, 0, 0)]})
        self.oa_number = oa_id
        self.iteam = iteam
        self.shade = shade
                
    @api.onchange('finish')
    def _onchange_finish(self):
        oa_id = None
        iteam = None
        shade = None
        finish = None
        if self.finish:
            oa_id = self.oa_number
            iteam = self.iteam
            shade = self.shade
            finish = self.finish
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.oa_number.id),
                ('shade', '=', self.shade.name),
                ('finish', '=', self.finish.name),
                ('next_operation', '=', 'Packing Output')
            ])
    
            if operations:
                # Size list
                unique_size = set(record.sizcommon for record in operations)
                size_records = self.env['selection.fields.data'].sudo().search([
                    ('field_name', '=', 'size')
                ])
                size_records.unlink()
    
                for _size in unique_size:
                    size_cr = self.env["selection.fields.data"].sudo().create({
                        'field_name': 'size',
                        'name': _size
                    })
                    self.update({'size': [(4, size_cr.name)]})  # Add the record to the Many2one field
            else:
                # Clear Size field if no operations are found
                self.update({'size': [(5, 0, 0)]})
        self.oa_number = oa_id
        self.iteam = iteam
        self.shade = shade
        self.finish = finish


    @api.onchange('size')
    
    def _onchange_size(self):
        oa_id = None
        iteam = None
        shade = None
        finish = None
        size = None
        qty = None
        
        if self.size:
            oa_id = self.oa_number
            iteam = self.iteam
            shade = self.shade
            finish = self.finish
            size = self.size
            qty = self.qty
            operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.oa_number.id),
                ('next_operation', '=', 'Packing Output'),
                ('shade', '=', self.shade.name),
                ('finish', '=', self.finish.name),
                ('sizcommon', '=', self.size.name), 
            ])
    
            if operations:
                qty = sum(operations.mapped('balance_qty'))
                # raise UserError(qty)  
                self.qty = qty
            else:
                # Clear Qty field if no operations are found
                self.qty = 0
        self.oa_number = oa_id
        self.iteam = iteam
        self.shade = shade
        self.finish = finish
        self.qty = qty
