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
_logger = logging.getLogger(__name__)


class LabelPrintingWizard(models.TransientModel):
    _name = 'label.print'
    _description = 'Label Printing'
    _check_company_auto = True
    
    # is_company = fields.Boolean(readonly=False, default=False)
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    report_type = fields.Selection([('pplg', 'Production Packing Label (General)'),('fgcl', 'FG Carton Label'),('pplo', 'Production Packing Label (Others)')], string='Report Type', required=True, help='Report Type', default='pplg')
    
    # company_name = fields.Char('Company Name', readonly=False, default='TEX ZIPPERS (BD) LIMITED')     
    # company_address = fields.Char('Company Address', readonly=False, default='Plot # 180, 264 & 273 Adamjee Export Processing Zone, Adamjee Nagar, Shiddhirgonj, Narayangonj, Bangladesh')  

    table_name = fields.Selection([('a', 'Table A'),('b', 'Table B')], string='Table', required=True, help='Table', default='a')
    Country_name = fields.Selection([('bangladesh', 'Bangladesh'),('vietnam', 'Vietnam'),('pakistan', 'Pakistan')], string='Country', required=True, help='Country', default='bangladesh')


    oa_number = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)

    iteam = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'Iteams')]", check_company=True, string='Iteam', store=True, required=False, readonly=False)
    shade = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'shade')]", check_company=True, string='Shade', store=True, required=False, readonly=False)
    finish = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'finish')]", check_company=True, string='Finish', store=True, required=False, readonly=False)
    size = fields.Many2one('selection.fields.data', domain="[('field_name', '=', 'size')]", check_company=True, string='Size', store=True, required=False, readonly=False)

    
    qty = fields.Char('Qty', readonly=False, default='')


    batch_lot = fields.Char('Batch/Lot', readonly=False, default='')
    qc_person = fields.Many2one('hr.employee', string="QC By", domain="['|', ('active', '=', True), ('department_id.id', '=', '89')]", index=True, required=True,readonly=False)
    
    # fil_qc_person = qc_person.filtered(lambda pr: pr.department_id.name == 'Quality Assurance.')
    # emp_fil = self.qc_person.filtered(lambda x: x.department_id = 'Quality Assurance')
    
    pre_check_person = fields.Many2one('hr.employee', "Pre-Check By",  required=True) #all perosns form pre-check dept
   
    printing_person = fields.Many2one('hr.employee', "Print By",  required=True) #all perosns form packing dept
    

    date_to = fields.Date('Date to', readonly=False, default=lambda self: self._compute_to_date())
    file_data = fields.Binary(readonly=True, attachment=False)
    
    @api.onchange('oa_number')
    def _onchange_oa_number(self):
        if self.oa_number:
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
                    self.update({'iteam': [(4, iteam_cr.id)]})  
    
                # Shade list
                unique_shade = set(record.shade for record in operations)
                shade_records = self.env['selection.fields.data'].sudo().search([
                    ('field_name', '=', 'shade')
                ])
                shade_records.unlink() 
    
                for _shade in unique_shade:
                    shade_cr = self.env["selection.fields.data"].sudo().create({
                        'field_name': 'shade',
                        'name': _shade
                    })
                    self.update({'shade': [(4, shade_cr.id)]}) 
    
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
                    self.update({'finish': [(4, finish_cr.id)]}) 
    
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
                    self.update({'size': [(4, size_cr.id)]}) 
    
            else:
                # Handle the case where no operations are found for the given oa_number
                # You may want to provide feedback to the user or handle this case differently
                pass




   