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
import calendar
from io import BytesIO
_logger = logging.getLogger(__name__)


class LabelPrintingWizard(models.TransientModel):
    _name = 'label.print'
    _description = 'Label Printing'
    _check_company_auto = True
    
    logo = "src/user/taps_sale/static/src/img/logo_tex_tiny.png" 
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    report_type = fields.Selection([('pplg', 'Production Packing Label (General)'),
                                    ('lpi', 'Label Print Information'),
                                    ('fgcl', 'FG Carton Label'),
                                    ('pplo', 'Production Packing Label (Others)')],
                                   string='Report Type', required=True, help='Report Type', default='pplg')
    company_name = fields.Char('Company Name', readonly=False, default='TEX ZIPPERS (BD) LIMITED')     
    company_address = fields.Char('Company Address', readonly=False, default='Plot # 180, 264 & 273 Adamjee Export Processing Zone, Adamjee Nagar, Shiddhirgonj, Narayangonj, Bangladesh')  

    table_name = fields.Selection([('A', 'Table A'),('B', 'Table B')], string='Table',  help='Table', default='A')
    
    Country_name = fields.Selection([('VIETNAM', 'Vietnam'),('PAKISTAN', 'Pakistan')], string='Country', help='Country', default='')
    
    lot_code = fields.Char('Lot Code', readonly=False)

    oa_number = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)
    
    iteam = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'Iteams')]", check_company=True, string='Iteam', store=True, readonly=False)
    # default=lambda self: self.get_default_iteam()
    
    shade = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'shade')]", check_company=True, string='Shade', store=True,  readonly=False)
    # ,default=lambda self: self.get_default_shade()
    
    finish = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'finish')]", check_company=True, string='Finish', store=True, readonly=False)
    # ,default=lambda self: self.get_default_finish()
    
    size = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'size')]", check_company=True, string='Size', store=True, readonly=False)
    # ,default=lambda self: self.get_default_size()
    
    qty = fields.Integer('Qty', readonly=False)

    batch_lot = fields.Char('Batch/Lot', readonly=False, default='')
    label_qty = fields.Integer( string="Label Qty", readonly=False)
    # ,compute='_compute_label_qty' 
    copy_of_print = fields.Integer('Label Copy', readonly=False, default = '1')
    
    qc_person = fields.Many2one('hr.employee', string="QC By", domain="[('active', '=', True), ('department_id', '=', 272)]", index=True, readonly=False)
    pre_check_person = fields.Many2one('hr.employee', string="Pre Check By", domain="[('active', '=', True), ('department_id', '=', 281)]", index=True, readonly=False)
    printing_person = fields.Many2one('hr.employee', string="Print By", domain="[('active', '=', True), ('department_id', '=', 284)]", index=True, readonly=False)
    


    # @api.model
    # def get_default_iteam(self):
    #     # Set your default value for 'Iteam' here
    #     return self.env['selection.fields.data'].search([('field_name', '=', 'Iteams')], limit=1).id

    # @api.model
    # def get_default_shade(self):
    #     # Set your default value for 'Shade' here
    #     return self.env['selection.fields.data'].search([('field_name', '=', 'shade')], limit=1).id

    # @api.model
    # def get_default_finish(self):
    #     # Set your default value for 'Finish' here
    #     return self.env['selection.fields.data'].search([('field_name', '=', 'finish')], limit=1).id

    # @api.model
    # def get_default_size(self):
    #     # Set your default value for 'Size' here
    #     return self.env['selection.fields.data'].search([('field_name', '=', 'size')], limit=1).id


    # @api.model
    # def onevent_lot(self,code=None):
    #     raise UserError(('thtth'))
    #     self.lot_code = ''
    #     self.lot_code = code
    #     return code    

    # @api.model
    # def get_production_details(self, code=None):
    #     production = self.env['operation.details'].search([('name', '=', code), ('name', '!=', None)])
    #     values = {}
    #     raise UserError(('fefoeij'))
    #     if production:
    #         values['lot_code'] = production[0].name
    #         values['qty'] = 5
    #         # values['oa_id'] = production[0].oa_id.id
    #         # values['item'] = production[0].fg_categ_type
    #         # values['shade'] = production[0].shade
    #         # values['finish'] = production[0].finish
    #         # values['output_of'] = production[0].work_center.name
    #         # values['planned_qty'] = production[0].qty
    #     return values    
    # #code for data input from barcode  

    @api.onchange('lot_code')
    def update_selection_fields_data(self):
        self.qty = 0
        # if self.lot_code:
            
            # operations = self.env['operation.details'].sudo().search([
            #     ('name', '=', self.lot_code),
            #     ('next_operation', '=', 'Packing Output'),
            # ])
            # if operations:
            #     # Iteam List
            #     unique_iteam = set(record.product_template_id.name for record in operations)
            #     iteam_records = self.env['selection.fields.data'].sudo().search([
            #         ('field_name', '=', 'Iteams')
            #     ])
            #     iteam_records.unlink()
    
            #     for _iteam in unique_iteam:
            #         iteam_cr = self.env["selection.fields.data"].sudo().create({
            #             'field_name': 'Iteams',
            #             'name': _iteam
            #         })
            #         self.update({'iteam': [(4, iteam_cr.name)]})
    
            #     # Shade list
            #     unique_shade = set(record.shade for record in operations)
            #     shade_records = self.env['selection.fields.data'].sudo().search([
            #         ('field_name', '=', 'shade')
            #     ])
            #     shade_records.unlink()  # Remove existing records
    
            #     for _shade in unique_shade:
            #         shade_cr = self.env["selection.fields.data"].sudo().create({
            #             'field_name': 'shade',
            #             'name': _shade
            #         })
            #         self.update({'shade': [(4, shade_cr.name)]})  # Add the record to the Many2one field
    
            #     # Finish list
            #     unique_finish = set(record.finish for record in operations)
            #     finish_records = self.env['selection.fields.data'].sudo().search([
            #         ('field_name', '=', 'finish')
            #     ])
            #     finish_records.unlink()
    
            #     for _finish in unique_finish:
            #         finish_cr = self.env["selection.fields.data"].sudo().create({
            #             'field_name': 'finish',
            #             'name': _finish
            #         })
            #         self.update({'finish': [(4, finish_cr.name)]})
    
            #     # Size list
            #     unique_size = set(record.sizcommon for record in operations)
            #     size_records = self.env['selection.fields.data'].sudo().search([
            #         ('field_name', '=', 'size')
            #     ])
            #     size_records.unlink()
    
            #     for _size in unique_size:
            #         size_cr = self.env["selection.fields.data"].sudo().create({
            #             'field_name': 'size',
            #             'name': _size
            #         })
            #         self.update({'size': [(4, size_cr.name)]})  # Add the record to the Many2one field
    
            #     self.iteam = iteam_cr[0].id
            #     self.shade = shade_cr[0].id
            #     self.finish = finish_cr[0].id
            #     self.size = size_cr[0].id
                # self.qty = 5

                


               
    # ...code for  label qty 
    @api.onchange('size')
    def _onchange_iteam(self):
        operations = self.env['operation.details'].sudo().search([
                ('oa_id', '=', self.oa_number.id)])
        self.label_qty = operations[0].product_template_id.pack_qty


    @api.onchange('qty', 'label_qty')
    def _compute_copy(self):
        # for record in self:
        if self.label_qty > 0:
            self.copy_of_print = self.qty / self.label_qty
        else:
            self.copy_of_print = 1

    
    # ---- 
    @api.onchange('oa_number')
    def _onchange_oa_number(self):
        oa_id = None
        item_id = None
        # shade = None
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
                    item_id = iteam_cr[0].id
                    # raise UserError((iteam_cr[0].name))
                    
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
                    shade = shade_cr[0].id
            else:
                # Clear Iteam field if no operations are found
                self.update({'iteam': [(5, 0, 0)]})
                self.update({'shade': [(5, 0, 0)]})
        self.oa_number = oa_id
        self.iteam = item_id
        # self.shade = shade
       
    
    @api.onchange('shade')
    def _onchange_shade(self):
        oa_id = None
        iteam = None
        shade = None
        finish = None
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
                    finish = finish_cr[0].id
            else:
                # Clear Finish field if no operations are found
                self.update({'finish': [(5, 0, 0)]})
        self.oa_number = oa_id
        self.iteam = iteam
        self.shade = shade
        self.finish = finish
                
    @api.onchange('finish')
    def _onchange_finish(self):
        oa_id = None
        iteam = None
        shade = None
        finish = None
        # size = None 
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
                    size = size_cr[0].id
            else:
                # Clear Size field if no operations are found
                self.update({'size': [(5, 0, 0)]})
        self.oa_number = oa_id
        self.iteam = iteam
        self.shade = shade
        self.finish = finish
        # self.size = size 


    @api.onchange('size')
    
    def _onchange_size(self):
        oa_id = None
        iteam = None
        # shade = None
        # finish = None
        # size = None
        # qty = None
        
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
        # self.shade = shade
        # self.finish = finish
        # self.qty = qty

  

    def generate_qweb_pdf(self):
        # Ensure that all required fields are filled
        # if not all([self.company_name, self.table_name, self.oa_number, self.iteam, self.finish, self.shade, self.size, self.qc_person, self.pre_check_person, self.printing_person, self.qty]):
        #     raise ValidationError("Please fill in all required fields before generating the PDF.")

        current_date = fields.Date.today()
        # Prepare data for the QWeb report
        data = {
            'logo': self.logo,
            'company_name': self.company_name,
            'company_address': self.company_address,
            'table_name': self.table_name,
            'date': current_date.strftime('%d-%b-%Y'),
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
            'copy_of_print':self.copy_of_print,
            'label_qty':self.label_qty,
            'Country_name':self.Country_name,
        }
        # raise UserError((self.printing_person.name))
        # print("Data Dictionary:", data)

        #Return the QWeb report action
        if self.report_type == 'pplg':
            if self.company_id.id == 1:
                return self.env.ref('taps_manufacturing.action_report_label_print').report_action(self, data=data)
            else:
                return self.env.ref('taps_manufacturing.action_report_label_print_mt').report_action(self, data=data)
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
        
        docs = self.env['operation.details'].sudo().search(domain, order='id desc',limit=1)
        
        store_label = self.env['label.print.data'].sudo().create({'name':docs.name,'batch_lot':data.get('batch_lot'),
                                                                  'table_name':data.get('table_name'),
                                                                  'qc_by':data.get('qc_person'),
                                                                  'pre_check_by':data.get('pre_check_person'),
                                                                  'print_by':data.get('printing_person'),
                                                                  'label_qty':data.get('label_qty'),
                                                                  'label_copy':data.get('copy_of_print')})     
        
        common_data = [
            data.get('logo'), #0
            data.get('company_name'), #1
            data.get('company_address'), #2
            data.get('table_name'), #3
            data.get('date'), #4
            data.get('batch_lot'), #5
            data.get('oa_number', '').replace('OAOO', ''), #6
            data.get('iteam'), #7
            data.get('finish'), #8
            data.get('shade'), #9
            data.get('size'), #10
            data.get('qc_person'), #11
            data.get('pre_check_person'),#12
            data.get('printing_person'),#13
            data.get('qty'), #14
            data.get('label_qty'), #15
            data.get('copy_of_print'), #16
            data.get('Country_name'), #17
            data.get(docs.partner_id.name), #18 Customer Name
            # data.get(docs.name), #15
                     
        ]
        common_data.append(common_data)
        # raise UserError((docs.partner_id.name))  
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'operation.details',
            'docs': docs,
            'datas': common_data,
            
        }

class LabelPrintPDF(models.AbstractModel):
    _name = 'report.taps_manufacturing.report_label_print_template_mt'
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
        
        docs = self.env['operation.details'].sudo().search(domain, order='id desc',limit=1)
        
        store_label = self.env['label.print.data'].sudo().create({'name':docs.name,'batch_lot':data.get('batch_lot'),
                                                                  'table_name':data.get('table_name'),
                                                                  'qc_by':data.get('qc_person'),
                                                                  'pre_check_by':data.get('pre_check_person'),
                                                                  'print_by':data.get('printing_person'),
                                                                  'label_qty':data.get('label_qty'),
                                                                  'label_copy':data.get('copy_of_print')})     
        
        common_data = [
            data.get('logo'), #0
            data.get('company_name'), #1
            data.get('company_address'), #2
            data.get('table_name'), #3
            data.get('date'), #4
            data.get('batch_lot'), #5
            data.get('oa_number', '').replace('OAOO', ''), #6
            data.get('iteam'), #7
            data.get('finish'), #8
            data.get('shade'), #9
            data.get('size'), #10
            data.get('qc_person'), #11
            data.get('pre_check_person'),#12
            data.get('printing_person'),#13
            data.get('qty'), #14
            data.get('label_qty'), #15
            data.get('copy_of_print'), #16
            data.get('Country_name'), #17
            data.get(docs.partner_id.name), #18 Customer Name
            # data.get(docs.name), #15
                     
        ]
        common_data.append(common_data)
        # raise UserError(docs.partner_id)  
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'operation.details',
            'docs': docs,
            'datas': common_data,
            
        }

 