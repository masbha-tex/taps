# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import base64
from datetime import datetime, timedelta, date

from odoo import api, fields, models, SUPERUSER_ID, _, exceptions
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
import re
from decimal import Decimal, ROUND_HALF_UP
import decimal
import logging
_logger = logging.getLogger(__name__)


class FgPacking(models.Model):
    _name = "fg.packing"
    _description = "Fg Packing"
    _check_company_auto = True

   
    name = fields.Char(string='Carton') # User Indput 
    carton_no = fields.Char(string='Carton No', store=True) # auto generated serial No
    carton_line = fields.One2many('fg.packing.line', 'fg_carton', string='Line',copy=True, auto_join=True)
    total_weight = fields.Char(string='Approximate Total Weight')
    qty = fields.Integer(string='Packet Qty', store=True)
    buyer_name = fields.Char(string='buyer_name')

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
    
    # @api.onchange('order_ref')
    # def _onchange_orderline_ids(self):
    #     if self.order_ref:
    #         self._create_oa()
    #     else:
    #         self.order_line = False #product_uom_qty
        
   
    # def get_cartoon_data_for_create(self):
    #     operation = self.env['operation.details'].sudo().search([
    #             ('name', '=', self.lot_code),
    #             ('next_operation', '=', 'Packing Output'),
    #         ])
    #     if operation:
    #         data = [
    #             data.get('l_code'), 
    #             data.get('cartoon_no'),   
    #             data.get('qty'), 
    #             data.get('total_weight'), 
    #             data.get(operation.oa_id.id),
    #             data.get(operation.buyer_name),
    #             data.get(operation.product_id.id),
    #             data.get(operation.product_template_id.id),
    #             data.get(datetime.now()),
    #             data.get(operation.shade),
    #             data.get(operation.shade_ref),
    #             data.get(operation.finish),
    #             data.get(operation.slidercodesfg),
    #             data.get(operation.top),
    #             data.get(operation.bottom),
    #             data.get(operation.pinbox),
    #             data.get(operation.sizcommon),
    #                      ]
    #     data.append(data)
    #     return {
    #         'doc_ids': operation.ids,
    #         'doc_model': 'operation.packing',
    #         'docs': operation,
    #         'datas': data,
            
    #     }
    
    # def store_cartoon_data(self):
    #     operation = self.env['operation.details'].sudo().search([
    #             ('name', '=', self.lot_code),
    #             ('next_operation', '=', 'Packing Output'),
    #         ])
    #     if operation:
    #         self.env['fg_packing.data'].sudo().create({
    #             'l_code':data.get('l_code'), 
    #             'cartoon_no':data.get('cartoon_no'),   
    #             'qty':data.get('qty'), 
    #             'total_weight':data.get('total_weight'), 
    #             'oa_id':data.get(operation.oa_id.id),
    #             'buyer_name':data.get(operation.buyer_name),
    #             'product_id':data.get(operation.product_id.id),
    #             'product_template_id':data.get(operation.product_template_id.id),
    #             'action_date':data.get(datetime.now()),
    #             'shade':data.get(operation.shade),
    #             'shade_ref':data.get(operation.shade_ref),
    #             'finish':data.get(operation.finish),
    #             'slidercodesfg':data.get(operation.slidercodesfg),
    #             'top':data.get(operation.top),
    #             'bottom':data.get(operation.bottom),
    #             'pinbox':data.get(operation.pinbox),
    #             'sizcommon':data.get(operation.sizcommon),
                         
    #         })


    
class FgPackingLine(models.Model):
    _name = "fg.packing.line"
    _description = "Packing Line"
    _check_company_auto = True
    
    l_code = fields.Many2one('operation.details', string='L Code', store=True)
    oa_id = fields.Char(string='OA',store=True)
    fg_carton = fields.Many2one('fg.packing', string='Carton ID', ondelete='cascade')    
    product_id = fields.Char(string='product_id',store=True)
    product_template_id = fields.Char(string='product_template_id',store=True)
    action_date = fields.Datetime(string='action_date',store=True)
    shade = fields.Char(string='shade',store=True)
    shade_ref = fields.Char(string='shade_ref',store=True)
    finish = fields.Char(string='finish',store=True)
    slidercodesfg = fields.Char(string='slidercodesfg',store=True)
    top = fields.Char(string='top',store=True)
    bottom = fields.Char(string='bottom',store=True)
    pinbox = fields.Char(string='pinbox',store=True)
    sizcommon = fields.Char(string='sizcommon',store=True)
    qty = fields.Char(string='qty',store=True)


    @api.onchange('l_code')
    def onchange_l_code(self):
        if self.l_code:
            # Assuming l_code is a Many2one field
            operation_details = self.l_code
            # operation_details = self.env['operation.details'].search([('name','=',l_code),('company_id','=',self.env.company.id)])

            # Update other fields based on the selected operation_details
            self.oa_id = operation_details.oa_id.name
            # self.fg_carton = operation_details.fg_carton
            self.product_id = operation_details.product_id
            self.product_template_id = operation_details.product_template_id
            self.action_date = operation_details.action_date
            self.shade = operation_details.shade
            self.shade_ref = operation_details.shade_ref
            self.finish = operation_details.finish
            self.slidercodesfg = operation_details.slidercodesfg
            self.top = operation_details.top
            self.bottom = operation_details.bottom
            self.pinbox = operation_details.pinbox
            self.sizcommon = operation_details.sizcommon
            self.qty = operation_details.done_qty