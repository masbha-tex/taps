import base64
import io
import logging
from odoo import models, fields, api
from odoo import http
from odoo import _
from werkzeug.wrappers import Response
from odoo.http import content_disposition, dispatch_rpc, request, route
from odoo.tools import pycompat
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from dateutil.relativedelta import relativedelta
import re
import math
from odoo.http import content_disposition
from odoo.tools import pycompat
import calendar
from io import BytesIO
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
_logger = logging.getLogger(__name__)


class LabelPrintingWizard(models.TransientModel):
    _name = 'label.print'
    _description = 'Label Printing'
    _check_company_auto = True
    
    logo = "src/user/taps_sale/static/src/img/logo_tex_tiny.png" 
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    report_type = fields.Selection([('pplg', 'Production Packing Label (General)'),
                                    ('fgcl', 'FG Carton Label'),
                                    ('pplo', 'Production Packing Label (Others)')],
                                   string='Report Type', required=True, help='Report Type', default='pplg')
    
    company_name = fields.Char('Company Name', readonly=False, default='TEX ZIPPERS (BD) LIMITED')     
    company_address = fields.Char('Company Address', readonly=False, default='Plot # 180, 264 & 273 Adamjee Export Processing Zone, Adamjee Nagar, Shiddhirgonj, Narayangonj, Bangladesh')  

    table_name = fields.Selection([('A', 'Table A'),('B', 'Table B')], string='Table', required=True, help='Table', default='A')
    Country_name = fields.Selection([('bangladesh', 'Bangladesh'),('vietnam', 'Vietnam'),('pakistan', 'Pakistan')], string='Country', required=True, help='Country', default='bangladesh')


    oa_number = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True,default='5552')

    iteam = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'Iteams')]", check_company=True, string='Iteam', store=True, required=False, readonly=False)
    shade = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'shade')]", check_company=True, string='Shade', store=True, required=False, readonly=False)
    finish = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'finish')]", check_company=True, string='Finish', store=True, readonly=False)
    size = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'size')]", check_company=True, string='Size', store=True, required=False, readonly=False)
    qty = fields.Integer('Qty', readonly=False, default='')

    batch_lot = fields.Char('Batch/Lot', readonly=False, default='000')
    
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


    def generate_qweb_pdf(self):
        # Ensure that all required fields are filled
        # if not all([self.company_name, self.table_name, self.oa_number, self.iteam, self.finish, self.shade, self.size, self.qc_person, self.pre_check_person, self.printing_person, self.qty]):
        #     raise ValidationError("Please fill in all required fields before generating the PDF.")

        # Prepare data for the QWeb report
        data = {
            'logo': self.logo,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'table_name': self.table_name,
            'date': fields.Date.today(),
            'batch_lot': self.batch_lot,
            'oa_number': self.oa_number.name,
            'iteam': self.iteam.name,
            'finish': self.finish.name,
            'shade': self.shade.name,
            'size': self.size.name,
            'qc_person': self.qc_person.name,
            'pre_check_person': self.pre_check_person.name,
            'printing_person': self.printing_person.name,
            'qty': self.qty,
        }
        # raise UserError((self.printing_person.name))
        # print("Data Dictionary:", data)

        #Return the QWeb report action
        if self.report_type == 'pplg':
            return self.env.ref('taps_manufacturing.action_report_label_print').report_action(self, data=data)
        else:
            raise ValidationError("Here is no PDF.")

class LabelPrintPDF(models.AbstractModel):
    _name = 'report.taps_manufacturing.report_label_print_template'
    _description = 'label print template'     

    def _get_report_values(self, docids, data=None):
        domain = []
        if data.get('oa_number'):
            domain.append(('oa_id', '=', data.get('oa_number')))
        if data.get('shade'):
            domain.append(('shade', '=', data.get('shade')))
        if data.get('finish'):
            domain.append(('finish', '=', data.get('finish')))
        if data.get('size'):
            domain.append(('sizcommon', '=', data.get('size')))
        domain.append(('next_operation', '=', 'Packing Output'))
        
        docs = self.env['operation.details'].sudo().search(domain)
        # raise UserError((docs.qty))
        
            
        common_data = [
            data.get('logo'), #0
            data.get('company_name'), #1
            data.get('company_address'), #2
            data.get('table_name'), #3
            data.get('date'), #4
            data.get('batch_lot'), #5
            data.get('oa_number'), #6
            data.get('iteam'), #7
            data.get('finish'), #8
            data.get('shade'), #9
            data.get('size'), #10
            data.get('qc_person'), #11
            data.get('pre_check_person'),#12
            data.get('printing_person'),#13
            data.get('qty'), #14
            # data.get(docs.name), #15
        ]
        common_data.append(common_data)
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'operation.details',
            'docs': docs,
            'datas': common_data,
            
        }

 
