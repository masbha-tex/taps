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


    
    l_code = fields.Char(string='Lot Code') # User Indput 
    total_weight = fields.Char(string='Approximate Weight') # cartoon weight 
    self = self.with_company(self.company_id) # Zipper or Unit 
    cartoon_no = fields.Integer(string='Cartoon No', store=True) # auto generated serial No
    qty = fields.Integer(string='Packet Qty', store=True) # qty from label 


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
   
    
    def _create_cartoon(self):
        operation = self.env['operation.details'].sudo().search([
                ('name', '=', self.lot_code),
                ('next_operation', '=', 'Packing Output'),
            ])
        if operation:
            self.env['fg.packing.data'].sudo().create({
                data.get('l_code'), 
                data.get('cartoon_no'),   
                data.get('qty'), 
                data.get('total_weight'), 
                data.get('oa_id':operation.oa_id.id,
                data.get('buyer_name':operation.buyer_name,
                data.get('product_id':operation.product_id.id,
                data.get('product_template_id':operation.product_template_id.id,
                data.get('action_date':datetime.now(),
                data.get('shade':operation.shade,
                data.get('shade_ref':operation.shade_ref,
                data.get('finish':operation.finish,
                data.get('slidercodesfg':operation.slidercodesfg,
                data.get('top':operation.top,
                data.get('bottom':operation.bottom,
                data.get('pinbox':operation.pinbox,
                data.get('sizein':operation.sizcommon,
                         
            })


    
  
  
