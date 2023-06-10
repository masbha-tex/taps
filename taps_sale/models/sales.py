# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from num2words import num2words

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import re


from werkzeug.urls import url_encode

class SaleOrder(models.Model):
    _inherit = "sale.order"
    
    priority_sales = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)
    buyer_name = fields.Many2one('sale.buyer', string='Buyer Name')
    season = fields.Char(string='Season')
    sample_ref = fields.Many2one('sale.order', string='Sample Ref.', readonly=False, domain=[('sales_type', '=', 'sample')])
    
    sales_type = fields.Selection([
            ('sample', 'Sample Order'),
            ('sale', 'Sales Order'),
            ('oa', 'OA')],
            string='Sales Type')
    invoice_details = fields.Char(string='Invoice Details', related='partner_invoice_id.contact_address_complete')
    delivery_details = fields.Char(string='Delivery Details', readonly=True, related='partner_shipping_id.contact_address_complete')
    po_no = fields.Char(string='PO No.')
    po_date = fields.Date(string='PO Date')
    revised_date = fields.Date(string=' PI Revised Date')
    pi_date = fields.Date(string='PI Date')
    order_type = fields.Char(string='Order Type')
    kind_attention = fields.Char(string='Kind Attention')
    hs_code = fields.Char(string='H.S Code')
    department = fields.Char(string='Department')
    division = fields.Char(string='Division')
    customer_ref = fields.Char(string='Customer Ref')
    production_type = fields.Char(string='Production Type')
    production_group = fields.Char(string='Production Group')
    style_ref = fields.Char(string='Style Ref.')
    order_ref = fields.Many2one('sale.order', string='Sales Order Ref.', readonly=True)
    remarks = fields.Text(string='Remarks')
    # others_note = fields.Text('Others Terms and conditions')
    bank = fields.Many2one('res.bank', string='Bank')
    # sales_person = fields.Many2one('hr.employee', string='Salesperson')
    pi_number = fields.Char(string='PI No.')
    # shipment_terms = fields.Char(string='Shipment Terms')
    shipment_mode = fields.Char(string='Shipment Mode')
    loading_place = fields.Char(string='Place of loading', default='AEPZ, NARAYANGANJ, BANGLADESH')
    destination_port = fields.Char(string='Destination Port')
    origin_country = fields.Char(string='Country of origin', default='BANGLADESH')
    validity_period = fields.Char(string='Period of validity')
    amount_in_word = fields.Char(string='Amount In Words' ,compute="_amount_in_words")
    # amount_in_word = num2words(amount_total, lang='en_IN')
    appr_weight = fields.Char(string='Approximate Weight')
    applicant_bank = fields.Text(string='Applicant Bank')
    sale_representative = fields.Many2one('sale.representative', string='Sales Representative')
    is_revised = fields.Boolean('Revision', tracking=True)
    revised_no = fields.Selection([
            ('r1', 'R1'),
            ('r2', 'R2'),
            ('r3', 'R3'),
            ('r4', 'R4'),
            ('r5', 'R5'),
            ('r6', 'R6'),
            ('r7', 'R7'),
            ('r8', 'R8'),
            ('r9', 'R9'),
            ('r10', 'R10')],
            string='Number of revision', tracking=True)
    pi_type = fields.Selection([
            ('regular', 'Regular'),
            ('block', 'Block'),
            ('replacement', 'Replacement'),],
            string='Type', default='regular')
    cause_of_revision = fields.Text(string='Cuase')
    cause_of_replacement = fields.Text(string='Replacement Cuase')
    is_hold = fields.Boolean('Hold', tracking=True)
    price_tracking = fields.Text('Price Tracker')
    avg_price = fields.Float(string='Average Price', compute="_compute_avg_price")
    avg_size = fields.Float(string='Average Size', compute="_compute_avg_size")
    assortment = fields.Char(string='Assortment')
    dpi = fields.Char(string='DPI')
    
    
    def _amount_in_words(self):
        total = 0.0
        for rec in self:
            total = format(rec.amount_total, ".2f")
            # raise UserError((total))
            # rec.amount_in_word = str (rec.currency_id.amount_to_text (total))
            # rec.amount_in_word = num2words(total)
            text = ''
            entire_num = int((str(total).split('.'))[0])
            decimal_num = int((str(total).split('.'))[1])       
            text+=num2words(entire_num, lang='en_IN')
            if entire_num == 1:
                text+=' dollar '
            else:
                text+=' dollars '
            if decimal_num > 0:
                text+=num2words(decimal_num, lang='en_IN')
                if decimal_num == 1:
                    text+=' cent '
                else:
                    text+=' cents '
            rec.amount_in_word = text.upper()
            


    
    #dlfkdjfk
    def _compute_avg_price (self): 
        for rec in self:
            if rec.amount_total>0:
                rec.avg_price = (rec.amount_total/sum(rec.order_line.mapped('product_uom_qty')))
            else:
                rec.avg_price = 0
                
    def _compute_avg_size (self): 
        for rec in self:
            line_count = len(rec.order_line)
            total_size = 0.0
            if line_count==0:
                line_count=1
            for line in rec.order_line:
                if line.sizein:
                    if line.sizein != 'N/A':
                        total_size += float(line.sizein)
                if line.sizecm:
                    if line.sizecm != 'N/A':
                        total_size += float(line.sizecm)
            rec.avg_size =(total_size/line_count)
    
    @api.onchange('order_ref')
    def _onchange_orderline_ids(self):
        if self.order_ref:
            self._create_oa()
        if self.order_ref:
            self._create_pi()
        else:
            self.order_line = False #product_uom_qty
    
    def _create_oa(self):
        for saleorder in self:
            if not saleorder.order_ref:
                continue
            saleorder.update({
                'company_id': saleorder.order_ref.company_id.id,
                'date_order': saleorder.order_ref.date_order,
                'pi_date': saleorder.order_ref.pi_date,
                'validity_date': saleorder.order_ref.validity_date,
                'require_signature': saleorder.order_ref.require_signature,
                'require_payment': saleorder.order_ref.require_payment,
                'partner_id': saleorder.order_ref.partner_id,
                'partner_invoice_id': saleorder.order_ref.partner_invoice_id,
                'partner_shipping_id': saleorder.order_ref.partner_shipping_id,
                'pricelist_id': saleorder.order_ref.pricelist_id,
                'currency_id': saleorder.order_ref.currency_id,
                'invoice_status': saleorder.order_ref.invoice_status,
                'invoice_details': saleorder.order_ref.invoice_details,
                'delivery_details': saleorder.order_ref.delivery_details,
                'note' : saleorder.order_ref.note,
                # 'others_note': saleorder.order_ref.others_note,
                'remarks' : saleorder.order_ref.remarks,
                'kind_attention' : saleorder.order_ref.kind_attention,
                'customer_ref' : saleorder.order_ref.customer_ref,
                'style_ref' : saleorder.order_ref.style_ref,
                'season' : saleorder.order_ref.season,
                'department' : saleorder.order_ref.department,
                'division' : saleorder.order_ref.division,
                'buyer_name': saleorder.order_ref.buyer_name,
                'hs_code': saleorder.order_ref.hs_code,
                'production_type' : saleorder.order_ref.production_type,
                'production_group' : saleorder.order_ref.production_group,
                'order_type' : saleorder.order_ref.order_type,
                'po_no' : saleorder.order_ref.po_no,
                'po_date' : saleorder.order_ref.po_date,
                'revised_date' : saleorder.order_ref.revised_date,
                'dpi' : saleorder.order_ref.dpi,
                'bank': saleorder.order_ref.bank,
                'incoterm' : saleorder.order_ref.incoterm,
                'shipment_mode' : saleorder.order_ref.shipment_mode,
                'loading_place' : saleorder.order_ref.loading_place,
                'destination_port' : saleorder.order_ref.destination_port,
                'origin_country' : saleorder.order_ref.origin_country,
                'validity_period' : saleorder.order_ref.validity_period,
                'sale_representative' : saleorder.order_ref.sale_representative.id
            })
            
            orderline = self.env['sale.order.line'].search([('order_id', '=', saleorder.order_ref.id)]).sorted(key = 'sequence')
            orderline_values = []
            for lines in orderline:
                orderline_values += [{
                    'order_id':self.id,
                    'name':lines.name,
                    'sequence':lines.sequence,
                    'invoice_lines':lines.invoice_lines,
                    'invoice_status':lines.invoice_status,
                    'price_unit':lines.price_unit,
                    'price_subtotal':lines.price_subtotal,
                    'price_tax':lines.price_tax,
                    'price_total':lines.price_total,
                    'price_reduce':lines.price_reduce,
                    'tax_id':lines.tax_id,
                    'price_reduce_taxinc':lines.price_reduce_taxinc,
                    'price_reduce_taxexcl':lines.price_reduce_taxexcl,
                    'discount':lines.discount,
                    'product_id':lines.product_id,
                    'product_template_id':lines.product_template_id,
                    'product_updatable':lines.product_updatable,
                    'product_uom_qty':lines.product_uom_qty,
                    'product_uom':lines.product_uom,
                    'product_uom_category_id':lines.product_uom_category_id,
                    'product_uom_readonly':lines.product_uom_readonly,
                    'product_custom_attribute_value_ids':lines.product_custom_attribute_value_ids,
                    'product_no_variant_attribute_value_ids':lines.product_no_variant_attribute_value_ids,
                    'qty_delivered_method':lines.qty_delivered_method,
                    'qty_delivered':lines.qty_delivered,
                    'qty_delivered_manual':lines.qty_delivered_manual,
                    'qty_to_invoice':lines.qty_to_invoice,
                    'qty_invoiced':lines.qty_invoiced,
                    'untaxed_amount_invoiced':lines.untaxed_amount_invoiced,
                    'untaxed_amount_to_invoice':lines.untaxed_amount_to_invoice,
                    'salesman_id':lines.salesman_id,
                    'currency_id':lines.currency_id,
                    'company_id':lines.company_id,
                    'order_partner_id':lines.order_partner_id,
                    'analytic_tag_ids':lines.analytic_tag_ids,
                    'analytic_line_ids':lines.analytic_line_ids,
                    'is_expense':lines.is_expense,
                    'is_downpayment':lines.is_downpayment,
                    'state':lines.state,
                    'customer_lead':lines.customer_lead,
                    'display_type':lines.display_type,
                    'id':lines.id,
                    'display_name':lines.display_name,
                    'create_uid':lines.create_uid,
                    'create_date':lines.create_date,
                    'write_uid':lines.write_uid,
                    'write_date':lines.write_date,
                    'sale_order_option_ids':lines.sale_order_option_ids,
                    'product_packaging':lines.product_packaging,
                    'route_id':lines.route_id,
                    'move_ids':lines.move_ids,
                    'product_type':lines.product_type,
                    'virtual_available_at_date':lines.virtual_available_at_date,
                    'scheduled_date':lines.scheduled_date,
                    'forecast_expected_date':lines.forecast_expected_date,
                    'free_qty_today':lines.free_qty_today,
                    'qty_available_today':lines.qty_available_today,
                    'warehouse_id':lines.warehouse_id,
                    'qty_to_deliver':lines.qty_to_deliver,
                    'is_mto':lines.is_mto,
                    'display_qty_widget':lines.display_qty_widget,
                    'purchase_line_ids':lines.purchase_line_ids,
                    'purchase_line_count':lines.purchase_line_count,
                    'is_delivery':lines.is_delivery,
                    'product_qty':lines.product_qty,
                    'recompute_delivery_price':lines.recompute_delivery_price,
                    'is_configurable_product':lines.is_configurable_product,
                    'product_template_attribute_value_ids':lines.product_template_attribute_value_ids,
                    'topbottom':lines.topbottom,
                    'slidercode':lines.slidercode,
                    'finish':lines.finish,
                    'shade':lines.shade,
                    'sizein':lines.sizein,
                    'sizecm':lines.sizecm,
                    'sizemm':lines.sizemm,
                    'logoref':lines.logoref,
                    'logo':lines.logo,
                    'logo_type':lines.logo_type,
                    'style_gmt':lines.style_gmt,
                    'shapefin':lines.shapefin,
                    'bcdpart':lines.bcdpart,
                    'b_part':lines.b_part,
                    'c_part':lines.c_part,
                    'd_part':lines.d_part,
                    'product_code':lines.product_code,
                    'shape':lines.shape,
                    'finish_ref':lines.finish_ref,
                    'nailmat':lines.nailmat,
                    'nailcap':lines.nailcap,
                    'fnamebcd':lines.fnamebcd,
                    'nu1washer':lines.nu1washer,
                    'nu2washer':lines.nu2washer,
                    'slidercodesfg':lines.slidercodesfg,
                    'dyedtape':lines.dyedtape,
                    'ptopfinish':lines.ptopfinish,
                    'numberoftop':lines.numberoftop,
                    'pbotomfinish':lines.pbotomfinish,
                    'ppinboxfinish':lines.ppinboxfinish,
                    'dippingfinish':lines.dippingfinish,
                    'gap':lines.gap,
                    'bom_id':lines.bom_id,
                    'tape_con':lines.tape_con,
                    'slider_con':lines.slider_con,
                    'topwire_con':lines.topwire_con,
                    'botomwire_con':lines.botomwire_con,
                    'wire_con':lines.wire_con,
                    'pinbox_con':lines.pinbox_con,
                }]            
            
            #saleorder.order_ref.order_line#
            saleorder.order_line = [(5, 0)] + [(0, 0, value) for value in orderline_values]

    def _create_pi(self):
        for saleorder in self:
            if not saleorder.order_ref:
                continue
            saleorder.update({
                'company_id': saleorder.order_ref.company_id.id,
                'date_order': saleorder.order_ref.date_order,
                'pi_date': saleorder.order_ref.pi_date,
                'validity_date': saleorder.order_ref.validity_date,
                'require_signature': saleorder.order_ref.require_signature,
                # 'require_payment': saleorder.order_ref.require_payment,
                'partner_id': saleorder.order_ref.partner_id,
                'partner_invoice_id': saleorder.order_ref.partner_invoice_id,
                'partner_shipping_id': saleorder.order_ref.partner_shipping_id,
                'pricelist_id': saleorder.order_ref.pricelist_id,
                'currency_id': saleorder.order_ref.currency_id,
                'invoice_status': saleorder.order_ref.invoice_status,
                'invoice_details': saleorder.order_ref.invoice_details,
                'delivery_details': saleorder.order_ref.delivery_details,
                'note' : saleorder.order_ref.note,
                # 'others_note': saleorder.order_ref.others_note,
                'remarks' : saleorder.order_ref.remarks,
                'kind_attention' : saleorder.order_ref.kind_attention,
                'customer_ref' : saleorder.order_ref.customer_ref,
                'style_ref' : saleorder.order_ref.style_ref,
                'season' : saleorder.order_ref.season,
                'department' : saleorder.order_ref.department,
                'division' : saleorder.order_ref.division,
                'buyer_name': saleorder.order_ref.buyer_name,
                'hs_code': saleorder.order_ref.hs_code,
                'production_type' : saleorder.order_ref.production_type,
                'production_group' : saleorder.order_ref.production_group,
                'order_type' : saleorder.order_ref.order_type,
                # 'po_no' : saleorder.order_ref.po_no,
                # 'po_date' : saleorder.order_ref.po_date,
                # 'revised_date' : saleorder.order_ref.revised_date,
                # 'dpi' : saleorder.order_ref.dpi,
                # 'bank': saleorder.order_ref.bank,
                'incoterm' : saleorder.order_ref.incoterm,
                'shipment_mode' : saleorder.order_ref.shipment_mode,
                'loading_place' : saleorder.order_ref.loading_place,
                'destination_port' : saleorder.order_ref.destination_port,
                'origin_country' : saleorder.order_ref.origin_country,
                'validity_period' : saleorder.order_ref.validity_period,
                'sale_representative' : saleorder.order_ref.sale_representative.id
            })
            
            orderline = self.env['sale.order.line'].search([('order_id', '=', saleorder.order_ref.id)]).sorted(key = 'sequence')
            orderline_values = []
            for lines in orderline:
                orderline_values += [{
                    'order_id':self.id,
                    'name':lines.name,
                    'sequence':lines.sequence,
                    'invoice_lines':lines.invoice_lines,
                    'invoice_status':lines.invoice_status,
                    'price_unit':lines.price_unit,
                    'price_subtotal':lines.price_subtotal,
                    'price_tax':lines.price_tax,
                    'price_total':lines.price_total,
                    'price_reduce':lines.price_reduce,
                    'tax_id':lines.tax_id,
                    'price_reduce_taxinc':lines.price_reduce_taxinc,
                    'price_reduce_taxexcl':lines.price_reduce_taxexcl,
                    'discount':lines.discount,
                    'product_id':lines.product_id,
                    'product_template_id':lines.product_template_id,
                    'product_updatable':lines.product_updatable,
                    'product_uom_qty':lines.product_uom_qty,
                    'product_uom':lines.product_uom,
                    'product_uom_category_id':lines.product_uom_category_id,
                    'product_uom_readonly':lines.product_uom_readonly,
                    'product_custom_attribute_value_ids':lines.product_custom_attribute_value_ids,
                    'product_no_variant_attribute_value_ids':lines.product_no_variant_attribute_value_ids,
                    'qty_delivered_method':lines.qty_delivered_method,
                    'qty_delivered':lines.qty_delivered,
                    'qty_delivered_manual':lines.qty_delivered_manual,
                    'qty_to_invoice':lines.qty_to_invoice,
                    'qty_invoiced':lines.qty_invoiced,
                    'untaxed_amount_invoiced':lines.untaxed_amount_invoiced,
                    'untaxed_amount_to_invoice':lines.untaxed_amount_to_invoice,
                    'salesman_id':lines.salesman_id,
                    'currency_id':lines.currency_id,
                    'company_id':lines.company_id,
                    'order_partner_id':lines.order_partner_id,
                    'analytic_tag_ids':lines.analytic_tag_ids,
                    'analytic_line_ids':lines.analytic_line_ids,
                    'is_expense':lines.is_expense,
                    'is_downpayment':lines.is_downpayment,
                    'state':lines.state,
                    'customer_lead':lines.customer_lead,
                    'display_type':lines.display_type,
                    'id':lines.id,
                    'display_name':lines.display_name,
                    'create_uid':lines.create_uid,
                    'create_date':lines.create_date,
                    'write_uid':lines.write_uid,
                    'write_date':lines.write_date,
                    'sale_order_option_ids':lines.sale_order_option_ids,
                    'product_packaging':lines.product_packaging,
                    'route_id':lines.route_id,
                    'move_ids':lines.move_ids,
                    'product_type':lines.product_type,
                    'virtual_available_at_date':lines.virtual_available_at_date,
                    'scheduled_date':lines.scheduled_date,
                    'forecast_expected_date':lines.forecast_expected_date,
                    'free_qty_today':lines.free_qty_today,
                    'qty_available_today':lines.qty_available_today,
                    'warehouse_id':lines.warehouse_id,
                    'qty_to_deliver':lines.qty_to_deliver,
                    'is_mto':lines.is_mto,
                    'display_qty_widget':lines.display_qty_widget,
                    'purchase_line_ids':lines.purchase_line_ids,
                    'purchase_line_count':lines.purchase_line_count,
                    'is_delivery':lines.is_delivery,
                    'product_qty':lines.product_qty,
                    'recompute_delivery_price':lines.recompute_delivery_price,
                    'is_configurable_product':lines.is_configurable_product,
                    'product_template_attribute_value_ids':lines.product_template_attribute_value_ids,
                    'topbottom':lines.topbottom,
                    'slidercode':lines.slidercode,
                    'finish':lines.finish,
                    'shade':lines.shade,
                    'sizein':lines.sizein,
                    'sizecm':lines.sizecm,
                    'sizemm':lines.sizemm,
                    'logoref':lines.logoref,
                    'logo':lines.logo,
                    'logo_type':lines.logo_type,
                    'style_gmt':lines.style_gmt,
                    'shapefin':lines.shapefin,
                    'bcdpart':lines.bcdpart,
                    'b_part':lines.b_part,
                    'c_part':lines.c_part,
                    'd_part':lines.d_part,
                    'product_code':lines.product_code,
                    'shape':lines.shape,
                    'finish_ref':lines.finish_ref,
                    'nailmat':lines.nailmat,
                    'nailcap':lines.nailcap,
                    'fnamebcd':lines.fnamebcd,
                    'nu1washer':lines.nu1washer,
                    'nu2washer':lines.nu2washer,
                    'slidercodesfg':lines.slidercodesfg,
                    'dyedtape':lines.dyedtape,
                    'ptopfinish':lines.ptopfinish,
                    'numberoftop':lines.numberoftop,
                    'pbotomfinish':lines.pbotomfinish,
                    'ppinboxfinish':lines.ppinboxfinish,
                    'dippingfinish':lines.dippingfinish,
                    'gap':lines.gap,
                    'bom_id':lines.bom_id,
                    'tape_con':lines.tape_con,
                    'slider_con':lines.slider_con,
                    'topwire_con':lines.topwire_con,
                    'botomwire_con':lines.botomwire_con,
                    'wire_con':lines.wire_con,
                    'pinbox_con':lines.pinbox_con,
                }]            
            
            #saleorder.order_ref.order_line#
            saleorder.order_line = [(5, 0)] + [(0, 0, value) for value in orderline_values]


    
    
    
#             orderline_values = []

#             product_qty = production.product_uom_id._compute_quantity(production.product_qty, production.bom_id.product_uom_id)
#             exploded_boms, dummy = production.bom_id.explode(production.product_id, product_qty / production.bom_id.product_qty, picking_type=production.bom_id.picking_type_id)

#             for bom, bom_data in exploded_boms:
#                 # If the operations of the parent BoM and phantom BoM are the same, don't recreate work orders.
#                 if not (bom.operation_ids and (not bom_data['parent_line'] or bom_data['parent_line'].bom_id.operation_ids != bom.operation_ids)):
#                     continue
#                 for operation in bom.operation_ids:
#                     orderline_values += [{
#                         'name': operation.name,
#                         'production_id': production.id,
#                         'workcenter_id': operation.workcenter_id.id,
#                         'product_uom_id': production.product_uom_id.id,
#                         'operation_id': operation.id,
#                         'state': 'pending',
#                         'consumption': production.consumption,
#                     }]

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        """
        Update the following fields when the partner is changed:
        - Pricelist
        - Payment terms
        - Invoice address
        - Delivery address
        - Sales Team
        """
        if not self.partner_id:
            self.update({
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'fiscal_position_id': False,
            })
            return

        self = self.with_company(self.company_id)

        ptid = self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False
        if self.order_ref:
            ptid = self.order_ref.payment_term_id.id
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': ptid,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        user_id = partner_user.id
        if not self.env.context.get('not_self_saleperson'):
            user_id = user_id or self.env.context.get('default_user_id', self.env.uid)
        if user_id and self.user_id.id != user_id:
            values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        if not self.env.context.get('not_self_saleperson') or not self.team_id:
            values['team_id'] = self.env['crm.team'].with_context(
                default_team_id=self.partner_id.team_id.id
            )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        self.update(values)


    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())
        #bom = self.env['mrp.bom']
        for orderline in self.order_line:
            bom = self.env['mrp.bom'].search([('product_id', '=', orderline.product_id.id)])
            # or_line = self.env['sale.order.line'].search([('product_id', '=', orderline.product_id.id),('slidercodesfg', '=', orderline.slidercodesfg),('dyedtape', '=', orderline.dyedtape),('ptopfinish', '=', orderline.ptopfinish),('numberoftop', '=', orderline.numberoftop),('pbotomfinish', '=', orderline.pbotomfinish),('ppinboxfinish', '=', orderline.ppinboxfinish),('dippingfinish', '=', orderline.dippingfinish),('sizein', '=', orderline.sizein),('sizecm', '=', orderline.sizecm),('gap', '=', orderline.gap)])
            #raise UserError((len(or_line)))
            #raise UserError((orderline))
            if bom:
                orderline.write({'bom_id':bom.id})
                continue
            else:
                bom_info = {
                    'code':'',
                    'active':True,
                    'type':'normal',
                    'product_tmpl_id':orderline.product_id.product_tmpl_id.id,
                    'product_id':orderline.product_id.id,
                    'product_qty':100,
                    'product_uom_id':orderline.product_id.product_tmpl_id.uom_id.id,
                    'sequence':'',
                    'ready_to_produce':'asap',
                    'picking_type_id':'',
                    'company_id':self.company_id.id,
                    'consumption':'warning',#expatt.store_fname,
                }
                bomrec = self.env['mrp.bom'].create(bom_info)
                bom_option = {}
                bom_option = {
                    'name':'Metal Assembly',
                    'workcenter_id':6,
                    'sequence':6,
                    'bom_id':bomrec.id,
                    'company_id':self.company_id.id,
                    'worksheet_type':'text',
                    'time_mode':'auto',
                    'time_mode_batch':10,
                    'time_cycle_manual':60
                }               
                process = []
                process.append(bom_option)
                bom_option = {}
                
                self.env['mrp.routing.workcenter'].create(process)
                wastage_percent = self.env['wastage.percent']
                seq = 0
                if orderline.slidercodesfg:
                    if orderline.slidercodesfg not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        consumption = 0.0
                        product_temp = self.env['product.template'].search([('name', '=', orderline.slidercodesfg)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type)]).sorted(key = 'id', reverse=False)[:1]
                        #result = contract.basic
                        if formula:
                            wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Slider')])
                        #inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                            formula_ = formula.slider_python_compute
                            #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))

                            consumption = safe_eval(formula_)# or 0.0, None, mode='exec', nocopy=True

                            #consumption = round(consumption,4)

                            if wastage_:
                                if wastage_.wastage>0:
                                    consumption += (consumption*wastage_.wastage)/100
                                    consumption = round(consumption*100,4)

                            bom_line_info = {
                                'product_id':product_.id,
                                'company_id':self.company_id.id,
                                'product_qty':consumption,
                                'product_uom_id':product_temp.uom_id.id,
                                'sequence':seq,
                                'bom_id':bomrec.id,
                                'operation_id':'',
                            }
                            self.env['mrp.bom.line'].create(bom_line_info)
                    
                
                if orderline.dyedtape:
                    tape = 'Dyeing C#'
                    if tape in orderline.dyedtape:
                        seq = seq + 1
                        size_type = "inch"
                        size = 0
                        consumption = 0.0
                        if orderline.sizein == "N/A":
                            size_type = "cm"
                            size = orderline.sizecm
                        else:
                            size = orderline.sizein
                        product_temp = self.env['product.template'].search([('name', '=', orderline.dyedtape)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type),('topbottom_type', '=', orderline.topbottom)])
                        if formula:
                            tape_type = 'Cotton'
                            if tape_type in orderline.dyedtape:
                                wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Cotton Tape')])
                            else:
                                wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Tape')])
                            #result = contract.basic
                            inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                            formula_ = formula.tape_python_compute
                            #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))
                            consumption = safe_eval(formula_, {'s': size, 'g': orderline.gap})# or 0.0, None, mode='exec', nocopy=True
                            #consumption = round(consumption,4)
                            if wastage_:
                                if wastage_.wastage>0:
                                    consumption += (consumption*wastage_.wastage)/100
                                    consumption = round(consumption*100,4)

                            bom_line_info = {
                                'product_id':product_.id,
                                'company_id':self.company_id.id,
                                'product_qty':consumption,
                                'product_uom_id':product_temp.uom_id.id,
                                'sequence':seq,
                                'bom_id':bomrec.id,
                                'operation_id':'',
                            }
                            self.env['mrp.bom.line'].create(bom_line_info)
                    
                    
                if orderline.ptopfinish:
                    if orderline.ptopfinish not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        consumption = 0.0
                        product_temp = self.env['product.template'].search([('name', 'like', orderline.ptopfinish)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type)])
                        wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Top')])
                        #result = contract.basic
                        inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                        #formula_ = formula.twair_python_compute
                        #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))
                        consumption = 100#safe_eval(formula_)# or 0.0, None, mode='exec', nocopy=True
                        #consumption = round(consumption,4)
                        if orderline.numberoftop:
                            if orderline.numberoftop == "Double":
                                consumption = consumption*2
                        if wastage_:
                            if wastage_.wastage>0:
                                consumption += (consumption*wastage_.wastage)/100
                                consumption = round(consumption,4)                    

                        bom_line_info = {
                            'product_id':product_.id,
                            'company_id':self.company_id.id,
                            'product_qty':consumption,
                            'product_uom_id':product_temp.uom_id.id,
                            'sequence':seq,
                            'bom_id':bomrec.id,
                            'operation_id':'',
                        }
                        self.env['mrp.bom.line'].create(bom_line_info)
                    

                if orderline.pbotomfinish:
                    if orderline.pbotomfinish not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        consumption = 0.0
                        product_temp = self.env['product.template'].search([('name', 'like', orderline.pbotomfinish)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type)])
                        wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Bottom')])
                        #result = contract.basic
                        inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                        #formula_ = formula.bwire_python_compute
                        #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))
                        consumption = 100#safe_eval(formula_)# or 0.0, None, mode='exec', nocopy=True
                        #consumption = round(consumption,4)
                        if wastage_:
                            if wastage_.wastage>0:
                                consumption += (consumption*wastage_.wastage)/100
                                consumption = round(consumption,4)       

                        bom_line_info = {
                            'product_id':product_.id,
                            'company_id':self.company_id.id,
                            'product_qty':consumption,
                            'product_uom_id':product_temp.uom_id.id,
                            'sequence':seq,
                            'bom_id':bomrec.id,
                            'operation_id':'',
                        }
                        self.env['mrp.bom.line'].create(bom_line_info)
                    
#                 if orderline.ppinboxfinish:
#                     if orderline.ppinboxfinish not in('TBA','N/A'):
#                         seq = seq + 1
#                         product_temp = self.env['product.template'].search([('name', 'like', orderline.ppinboxfinish)]).sorted(key = 'id', reverse=True)[:1]
#                         product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

#                         bom_line_info = {
#                             'product_id':product_.id,
#                             'company_id':self.company_id.id,
#                             'product_qty':1,
#                             'product_uom_id':product_temp.uom_id.id,
#                             'sequence':seq,
#                             'bom_id':bomrec.id,
#                             'operation_id':'',
#                         }
#                         self.env['mrp.bom.line'].create(bom_line_info)
                

                if orderline.topbottom:
                    if orderline.topbottom not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        consumption = 0.0
                        p_type = ''
                        if 'COIL 3' in orderline.product_id.product_tmpl_id.name:
                            p_type = 'C#3'
                        elif 'COIL 5' in orderline.product_id.product_tmpl_id.name:
                            p_type = 'C#5'
                        elif 'PLASTIC 3' in orderline.product_id.product_tmpl_id.name:
                            p_type = 'P#3'
                        elif 'PLASTIC 5' in orderline.product_id.product_tmpl_id.name:
                            p_type = 'P#5'
                            
                        product_temp = self.env['product.template'].search([('name', 'like', orderline.topbottom),('name', 'like', p_type)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type),('topbottom_type', '=', orderline.topbottom)])
                        wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Bottom')])
                        #result = contract.basic
                        inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                        #formula_ = formula.tbwire_python_compute
                        #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))
                        consumption = 100#safe_eval(formula_)# or 0.0, None, mode='exec', nocopy=True
                        #consumption = round(consumption,4)
                        if wastage_:
                            if wastage_.wastage>0:
                                consumption += (consumption*wastage_.wastage)/100
                                consumption = round(consumption,4)       

                        bom_line_info = {
                            'product_id':product_.id,
                            'company_id':self.company_id.id,
                            'product_qty':consumption,
                            'product_uom_id':product_temp.uom_id.id,
                            'sequence':seq,
                            'bom_id':bomrec.id,
                            'operation_id':'',
                        }
                        self.env['mrp.bom.line'].create(bom_line_info)                
                
                
                if orderline.dippingfinish:
                    if orderline.dippingfinish not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        size = 0
                        consumption = 0.0
                        if orderline.sizein == "N/A":
                            size_type = "cm"
                            size = orderline.sizecm
                        else:
                            size = orderline.sizein
                        product_temp = self.env['product.template'].search([('name', 'like', orderline.dippingfinish)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                        

                        
                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type)])
                        wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Wire')])
                        wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Tape')])
                        #result = contract.basic
                        inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                        
                        
                        formula_ = formula.wair_python_compute
                        formula_tape = formula.tape_python_compute                       

                        consumption = safe_eval(formula_, {'s': size})# or 0.0, None, mode='exec', nocopy=True
                        consumption_tape = safe_eval(formula_tape, {'s': size, 'g': orderline.gap})
                        #consumption += consumption_tape

                        #consumption = round(consumption,4)
                        consumption_ = 0
                        if wastage_:
                            if wastage_.wastage>0:
                                consumption += (consumption*wastage_.wastage)/100
                                consumption_tape += (consumption_tape*wastage_tape.wastage)/100
                                consumption_ = round(((consumption*100) + (consumption_tape*100)),4)

                        bom_line_info = {
                            'product_id':product_.id,
                            'company_id':self.company_id.id,
                            'product_qty':consumption_,
                            'product_uom_id':product_temp.uom_id.id,
                            'sequence':seq,
                            'bom_id':bomrec.id,
                            'operation_id':'',
                        }
                        self.env['mrp.bom.line'].create(bom_line_info)
                    
                if orderline.ppinboxfinish:
                    if orderline.ppinboxfinish not in('TBA','N/A'):
                        seq = seq + 1
                        size_type = "inch"
                        size = 0
                        consumption = 0.0
                        if orderline.sizein == "N/A":
                            size_type = "cm"
                            size = orderline.sizecm
                        else:
                            size = orderline.sizein
                        product_temp = self.env['product.template'].search([('name', 'like', orderline.ppinboxfinish)]).sorted(key = 'id', reverse=True)[:1]
                        product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]

                        #product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('unit_type', '=', size_type)]).sorted(key = 'id', reverse=False)[:1]
                        wastage_ = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Pinbox')])
                        #result = contract.basic
                        inner_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', product_.product_tmpl_id.id)])
                        #formula_ = formula.pinbox_python_compute
                        #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))

                        consumption = 100#safe_eval(formula_)# or 0.0, None,pinbox_python_compute mode='exec', nocopy=True

                        #consumption = round(consumption,4)
                        if wastage_:
                            if wastage_.wastage>0:
                                consumption += (consumption*wastage_.wastage)/100
                                consumption = round(consumption,4)                    

                        bom_line_info = {
                            'product_id':product_.id,
                            'company_id':self.company_id.id,
                            'product_qty':consumption,
                            'product_uom_id':product_temp.uom_id.id,
                            'sequence':seq,
                            'bom_id':bomrec.id,
                            'operation_id':'',
                        }
                        self.env['mrp.bom.line'].create(bom_line_info)                    
                    
                orderline.write({'bom_id':bomrec.id})
                
#                 order_point = {
#                     'name':'Replenishment Report',
#                     'trigger':'manual',
#                     'active':True,
#                     'warehouse_id':1,
#                     'location_id':8,
#                     'product_id':orderline.product_id.id,
#                     'product_category_id':orderline.product_id.categ_id.id,
#                     'product_min_qty':0,
#                     'product_max_qty':0,
#                     'qty_multiple':1,
#                     #'group_id':0.0,
#                     'company_id':self.company_id.id,
#                     'route_id':1,
#                     'qty_to_order':orderline.product_uom_qty,
#                     'bom_id':bomrec.id,
#                     #'supplier_id':0.0,
#                     'sale_order_line':orderline.id,
#                     'sale_order_id':orderline.order_id.id
#                 }
#                 self.env['stock.warehouse.orderpoint'].create(order_point)

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        
        context = self._context.copy()
        context.pop('default_name', None)
        
        if self.sales_type == 'oa':
            self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        if self.sales_type == 'oa':
            self.order_line.product_consumption(self.id)
            self.order_line.compute_shadewise_tape()
            #self.generate_mrp()
            #self.order_line.compute_shadewise_tape()
            
        return True
    def mrp_values(self,id,product,qty,uom,bom):
        values = {
            'priority': 0,
            'product_id': product,
            'product_qty': qty,
            'product_uom_id': uom,
            #'qty_producing': 0,
            'product_uom_qty': qty,
            'picking_type_id': 8,
            'location_src_id': 8,
            'location_dest_id': 8,
            'date_planned_start': datetime.now(),
            'date_planned_finished': datetime.now() + timedelta(hours=1),
            'date_deadline': datetime.now() + timedelta(hours=1),
            'bom_id': bom,
            'state': 'draft',
            #'user_id': self.company_id.id,
            'company_id': self.company_id.id,
            #'procurement_group_id': self.company_id.id,
            'propagate_cancel': False,
            'is_locked': False,
            'production_location_id': 15,
            'consumption': 'warning',
            'oa_id':self.id,
            'sale_order_line':id
        }
        return values
        
    def generate_mrp(self):
        unique_shade = []
        for products in self.order_line:
            mrp_production = self.env['mrp.production'].create(self.mrp_values(products.id,products.product_id.id,products.product_qty,products.product_uom.id,products.bom_id))
            mrp_production.move_raw_ids.create(mrp_production._get_moves_raw_values())
            mrp_production._onchange_workorder_ids()
            mrp_production._create_update_move_finished()
            bom_lines = self.env['mrp.bom.line'].search([('bom_id','=',products.bom_id)])
            #raise UserError((products.bom_id))
            for lines in bom_lines:
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id)])
                qty = (lines.product_qty/100) * products.product_qty
                mrp_sf_production = self.env['mrp.production'].create(self.mrp_values(products.id,lines.product_id.id,qty,lines.product_uom_id.id,bom.id))
                mrp_sf_production.move_raw_ids.create(mrp_sf_production._get_moves_raw_values())
                mrp_sf_production._onchange_workorder_ids()
                mrp_sf_production._create_update_move_finished()
                bom_sub_lines = self.env['mrp.bom.line'].search([('bom_id','=',bom.id)])
                #raise UserError((products.product_id.id,lines.product_id.id,sub_lines.product_id.id))
                for sub_lines in bom_sub_lines:
                    #code = 'SFG' #fullstring.find(substring)
                    #productcode = sub_lines.product_id.default_code
                    
                    #findcode = "SFG" in productcode #productcode.find(code)
                    #raise UserError((findcode))
                    # if "SFG" in productcode:
                    #     raise UserError((productcode))
                    sub_bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', sub_lines.product_id.product_tmpl_id.id)])
                    if sub_bom:
                        product_qty = products.product_qty
                        
                        filtered_shade = [x for x in unique_shade if x[0] == products.product_id.product_tmpl_id.id and x[1] == products.shade]
                        if filtered_shade:
                            #raise UserError((filtered_shade,'sdfdf'))
                            a = 'a'
                        else:
                            #raise UserError((filtered_shade))
                            same_shade = self.order_line.filtered(lambda sol: sol.product_id.product_tmpl_id.id == products.product_id.product_tmpl_id.id and sol.shade == products.shade)
                            product_qty = sum(same_shade.mapped('product_qty'))
                            #raise UserError(((sub_lines.product_qty/100),product_qty))
                            sub_qty = (sub_lines.product_qty/100) * product_qty

                            sub_production = self.env['mrp.production'].create(self.mrp_values(products.id,sub_lines.product_id.id,sub_qty,sub_lines.product_uom_id.id,sub_bom.id))
                            sub_production.move_raw_ids.create(sub_production._get_moves_raw_values())
                            sub_production._onchange_workorder_ids()
                            sub_production._create_update_move_finished()
                            sub_production.action_confirm()
                            
                        _shade = []
                        _shade = [products.product_id.product_tmpl_id.id,products.shade]
                        unique_shade.append(_shade)
                        
                mrp_sf_production.action_confirm()
            mrp_production.action_confirm()
            products.product_id.product_tmpl_id.button_bom_cost()

            
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date_order' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            #vals['name'] = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _('New')

            if vals.get('sales_type') == "sample":
                ref = self.env['ir.sequence'].next_by_code('sale.order.sa', sequence_date=seq_date) or _('New')
                vals['name'] = ref
            if vals.get('sales_type') == "sale":
                ref = self.env['ir.sequence'].next_by_code('sale.order', sequence_date=seq_date) or _('New')
                vals['name'] = ref
                if vals.get('company_id') == 1:
                    vals['pi_number'] = ref.replace("S", "Z")
                if vals.get('company_id') == 3:
                    vals['pi_number'] = ref.replace("S", "B")
                    
            if vals.get('sales_type') == "oa":
                ref = self.env['ir.sequence'].next_by_code('sale.order.oa', sequence_date=seq_date) or _('New')
                vals['name'] = ref
                vals['pi_number'] = ref.replace("OA", 'PI')
                
        # Makes sure partner_invoice_id', 'partner_shipping_id' and 'pricelist_id' are defined
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id', 'pricelist_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            vals['pricelist_id'] = vals.setdefault('pricelist_id', partner.property_product_pricelist.id)
        result = super(SaleOrder, self).create(vals)
        return result
            
    # def _action_confirm(self):
    #     self.order_line._action_launch_stock_rule()
    #     return super(SaleOrder, self)._action_confirm()

    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    topbottom = fields.Text(string='Top/Bottom', store=True)
    slidercode = fields.Text(string='Slider Code', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    sizemm = fields.Text(string='Size (MM)', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', store=True)
    
    numberoftop = fields.Text(string='Number of Top', store=True)
    
    pbotomfinish = fields.Text(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', store=True)
    gap = fields.Text(string='Gap', store=True)
    logo = fields.Text(string='Logo', store=True)
    logoref = fields.Text(string='Logo Ref', store=True)
    logo_type = fields.Text(string='Logo Type', store=True)
    style_gmt = fields.Text(string='Style/GMT', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    b_part = fields.Text(string='B Part', store=True)
    c_part = fields.Text(string='C Part', store=True)
    d_part = fields.Text(string='D Part', store=True)
    finish_ref = fields.Text(string='Finish Ref', store=True)
    product_code = fields.Text(string='Product Code', store=True)
    shape = fields.Text(string='Shape', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    bom_id = fields.Integer('Bom Id', copy=True, store=True)
    
    tape_con = fields.Float('Tape Consumption', required=True, digits='Unit Price', default=0.0)
    slider_con = fields.Float('Slider Consumption', required=True, digits='Unit Price', default=0.0)
    topwire_con = fields.Float('Topwire Consumption', required=True, digits='Unit Price', default=0.0)
    botomwire_con = fields.Float('Botomwire Consumption', required=True, digits='Unit Price', default=0.0)
    tbwire_con = fields.Float('TBwire Consumption', required=True, digits='Unit Price', default=0.0)
    wire_con = fields.Float('Wire Consumption', required=True, digits='Unit Price', default=0.0)
    pinbox_con = fields.Float('Pinbox Consumption', required=True, digits='Unit Price', default=0.0)
    shadewise_tape = fields.Float('Shadwise Tape', required=True, digits='Unit Price', default=0.0, compute='compute_shadewise_tape', compute_sudo=True, store=True)
    color = fields.Integer(string='Color')
    #def write
  
    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(product_id=False, price_unit=0, product_uom_qty=0, product_uom=False, customer_lead=0)

            product_t = self.env['product.product'].search([('id', '=', values.get('product_id'))])
            wastage_percent = self.env['wastage.percent']
            size_type = "inch"
            size = 0
            consumption = 0.0
            if values.get('sizein') == "N/A":
                size_type = "cm"
                size = values.get('sizecm')
            else:
                size = values.get('sizein')
            if values.get('topbottom'):
                formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', product_t.product_tmpl_id.id),('unit_type', '=', size_type),('topbottom_type', '=', values.get('topbottom'))])
            else:
                formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', product_t.product_tmpl_id.id),('unit_type', '=', size_type)])
            tape_type = 'Cotton'
            if values.get('dyedtape'):
                if tape_type in values.get('dyedtape'):
                    wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Cotton Tape')])
                else:
                    wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Tape')])
            else:
                wastage_tape = False
            wastage_slider = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Slider')])
            wastage_top = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Top')])
            wastage_bottom = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Bottom')])
            wastage_wire = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Wire')])
            wastage_pinbox = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Pinbox')])

            con_tape = con_wire = con_slider = con_top = con_bottom = con_pinboc = 0 
            
            if formula:
                if formula.tape_python_compute:
                    con_tape = safe_eval(formula.tape_python_compute, {'s': size, 'g': values.get('gap')})
                    if wastage_tape:
                        if wastage_tape.wastage>0:
                            con_tape += (con_tape*wastage_tape.wastage)/100
                    values['tape_con'] = round(con_tape*values.get('product_uom_qty'),4)

                if formula.wair_python_compute:
                    con_wire = safe_eval(formula.wair_python_compute, {'s': size})
                    if wastage_wire:
                        if wastage_wire.wastage>0:
                            con_wire += (con_wire*wastage_wire.wastage)/100
                    values['wire_con'] = round(con_wire*values.get('product_uom_qty'),4)
                if formula.slider_python_compute:
                    con_slider = safe_eval(formula.slider_python_compute)
                    if wastage_slider:
                        if wastage_slider.wastage>0:
                            con_slider += (con_slider*wastage_slider.wastage)/100
                    values['slider_con'] = round(con_slider*values.get('product_uom_qty'),4)
                if formula.twair_python_compute:
                    con_top = safe_eval(formula.twair_python_compute)
                    if wastage_top:
                        if wastage_top.wastage>0:
                            con_top += (con_top*wastage_top.wastage)/100
                    values['topwire_con'] = round(con_top*values.get('product_uom_qty'),4)
                if formula.bwire_python_compute:
                    con_bottom = safe_eval(formula.bwire_python_compute)
                    if wastage_bottom:
                        if wastage_bottom.wastage>0:
                            con_bottom += (con_bottom*wastage_bottom.wastage)/100
                    values['botomwire_con'] = round(con_bottom*values.get('product_uom_qty'),4)
                if formula.tbwire_python_compute:
                    con_bottom = safe_eval(formula.tbwire_python_compute)
                    if wastage_bottom:
                        if wastage_bottom.wastage>0:
                            con_bottom += (con_bottom*wastage_bottom.wastage)/100
                    values['tbwire_con'] = round(con_bottom*values.get('product_uom_qty'),4)
                if formula.pinbox_python_compute:
                    con_pinbox = safe_eval(formula.pinbox_python_compute)
                    if wastage_pinbox:
                        if wastage_pinbox.wastage>0:
                            con_pinbox += (con_pinbox*wastage_pinbox.wastage)/100
                    values['pinbox_con'] = round(con_pinbox*values.get('product_uom_qty'),4)
            else:
                values['tape_con'] = values['wire_con'] = values['slider_con'] = values['topwire_con'] = values['botomwire_con'] = values['tbwire_con'] = values['pinbox_con'] = 0
            
            values.update(self._prepare_add_missing_fields(values))
        lines = super().create(vals_list)
        for line in lines:
            if line.product_id and line.order_id.state == 'sale':
                msg = _("Extra line with %s ") % (line.product_id.display_name,)
                line.order_id.message_post(body=msg)
                # create an analytic account if at least an expense product
                if line.product_id.expense_policy not in [False, 'no'] and not line.order_id.analytic_account_id:
                    line.order_id._create_analytic_account()
        return lines    
    
    
    def duplicate_line(self):
        max_seq = max(line.sequence for line in self.order_id.order_line)
        self.copy({'order_id': self.order_id.id, 'sequence': max_seq + 1})
        
        
        
    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv
        
        # remove the no_variant attributes that don't belong to this template
        
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav
        
        vals = {}
        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        lang = get_lang(self.env, self.order_id.partner_id.lang).code
        product = self.product_id.with_context(
            lang=lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        vals.update(name=self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product))
        
        #raise UserError((self.product_id.combination_indices))
        #productname = self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product)
        test_string = str(self.product_id.combination_indices)
        temp = re.findall(r'\d+', test_string)
        res = list(map(int, temp))
        atv = self.env['product.template.attribute.value'].search([('id', 'in', res)])
        
        for rec in atv:
            if rec.attribute_id.name == 'Top / Bottom':
                self.topbottom = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Slider Code':
                self.slidercode = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Slider Code (SFG)':
                self.slidercodesfg = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Finish':
                name = rec.product_attribute_value_id.name
                custom_values = self.product_custom_attribute_value_ids.filtered(lambda p: p.custom_product_template_attribute_value_id.id == rec.id)
                if custom_values.custom_value:
                    name += "\n" + custom_values.custom_value
                self.finish = name
                continue
            if rec.attribute_id.name == 'Shade':
                name = rec.product_attribute_value_id.name
                custom_values = self.product_custom_attribute_value_ids.filtered(lambda p: p.custom_product_template_attribute_value_id.id == rec.id)
                if custom_values.custom_value:
                    name += "\n" + custom_values.custom_value
                self.shade = name
                continue
            if rec.attribute_id.name == 'Size (Inch)':
                self.sizein = rec.product_attribute_value_id.name
                if rec.product_attribute_value_id.name !='N/A':
                    self.gap = self.product_id.product_tmpl_id.gap_inch
                continue
            if rec.attribute_id.name == 'Size (CM)':
                self.sizecm = rec.product_attribute_value_id.name
                if rec.product_attribute_value_id.name !='N/A':
                    self.gap = self.product_id.product_tmpl_id.gap_cm
                continue
            if rec.attribute_id.name == 'Size (MM)':
                self.sizemm = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Dyed Tape':
                self.dyedtape = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Top Finish':
                self.ptopfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Number of Top':
                self.numberoftop = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Bottom Finish':
                self.pbotomfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Pin-Box Finish':
                self.ppinboxfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Dipping Finish':
                self.dippingfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Logo Ref':
                self.logoref = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Style/Gmt':
                self.style_gmt = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Logo ':
                self.logo = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Logo Type':
                self.logo_type = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Shape Finish':
                self.shapefin = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Finish Ref':
                self.finish_ref = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'BCD Part Material Type / Size':
                self.bcdpart = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'B Part':
                self.b_part = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'C Part':
                self.c_part = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'D Part':
                self.d_part = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Product Code':
                self.product_code = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Shape':
                self.shape = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Nail Material / Type / Shape / Size':
                self.nailmat = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Nail Cap Logo':
                self.nailcap = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Finish Name ( BCD/NAIL/ NAIL CAP)':
                self.fnamebcd = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == '1 NO. Washer Material & Size':
                self.nu1washer = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == '2 NO. Washer Material & Size':
                self.nu2washer = rec.product_attribute_value_id.name
                continue
                
        self._compute_tax_id()
        self.update(vals)

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s", product.name)
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result
        # if self.order_id.pricelist_id and self.order_id.partner_id:
        #     vals['price_unit'] = product._get_tax_included_unit_price(
        #         self.company_id,
        #         self.order_id.currency_id,
        #         self.order_id.date_order,
        #         'sale',
        #         fiscal_position=self.order_id.fiscal_position_id,
        #         product_price_unit=self._get_display_price(product),
        #         product_currency=self.order_id.currency_id
        #     )
    


    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        return product.get_product_multiline_description_sale()# + self._get_sale_order_line_multiline_description_variants()
  

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_("You cannot change the type of a sale order line. Instead you should delete the current line and create a new line of the proper type."))

        if 'product_uom_qty' in values:
            precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            self.filtered(
                lambda r: r.state == 'sale' and float_compare(r.product_uom_qty, values['product_uom_qty'], precision_digits=precision) != 0)._update_line_quantity(values)

        # Prevent writing on a locked SO.
        protected_fields = self._get_protected_fields()
        if 'done' in self.mapped('order_id.state') and any(f in values.keys() for f in protected_fields):
            protected_fields_modified = list(set(protected_fields) & set(values.keys()))
            fields = self.env['ir.model.fields'].search([
                ('name', 'in', protected_fields_modified), ('model', '=', self._name)
            ])
            raise UserError(
                _('It is forbidden to modify the following fields in a locked order:\n%s')
                % '\n'.join(fields.mapped('field_description'))
            )
        
        result = super(SaleOrderLine, self).write(values)
        return result

    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        else:
            all_line = self.env['sale.order.line'].search([('order_id', '=', self.mapped('order_id').id),('id', 'not in', self.mapped('id'))])
        if all_line:
            row = 0
            for line in all_line[row:]:
                all_id = []
                s_total = 0
                for l in all_line[row:]:
                    if (l.product_id.product_tmpl_id.id == line.product_id.product_tmpl_id.id and l.finish == line.finish and l.shade == line.shade):
                        s_total += l.tape_con
                        all_id.append(l.id)
                        row += 1
                        if len(all_line) == row:
                            all_tape = all_line.filtered(lambda sol: sol.id in all_id)
                            all_tape.update({'shadewise_tape':s_total})
                    else:
                        all_tape = all_line.filtered(lambda sol: sol.id in all_id)
                        all_tape.update({'shadewise_tape':s_total})
                        break
        return super(SaleOrderLine, self).unlink()
    
    
    @api.depends('product_uom_qty','finish','shade','sequence')
    def compute_shadewise_tape(self):
        all_line = self.env['sale.order.line'].search([('order_id', '=', self.mapped('order_id').id)])
        if all_line:
            row = 0
            for line in all_line[row:]:
                all_id = []
                s_total = 0
                for l in all_line[row:]:
                    if (l.product_id.product_tmpl_id.id == line.product_id.product_tmpl_id.id and l.finish == line.finish and l.shade == line.shade):
                        s_total += l.tape_con
                        all_id.append(l.id)
                        row += 1
                        if len(all_line) == row:
                            all_tape = all_line.filtered(lambda sol: sol.id in all_id)
                            all_tape.update({'shadewise_tape':s_total})
                    else:
                        all_tape = all_line.filtered(lambda sol: sol.id in all_id)
                        all_tape.update({'shadewise_tape':s_total})
                        break
        
    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        a = 'a'
        wastage_percent = self.env['wastage.percent']
        size_type = "inch"
        size = 0
        consumption = 0.0
        if self.sizein == "N/A":
            size_type = "cm"
            size = self.sizecm
        else:
            size = self.sizein
        if self.topbottom:
            formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),('unit_type', '=', size_type),('topbottom_type', '=', self.topbottom)])
        else:
            formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),('unit_type', '=', size_type)])
        
        if formula:
            tape_type = 'Cotton'
            if self.dyedtape:
                if tape_type in self.dyedtape:
                    wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Cotton Tape')])
                else:
                    wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Tape')])
            
            else:
                wastage_tape = False

            wastage_slider = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Slider')])
            wastage_top = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Top')])
            wastage_bottom = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Bottom')])
            wastage_wire = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Wire')])
            wastage_pinbox = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Pinbox')])

            con_tape = con_wire = con_slider = con_top = con_bottom = con_pinboc = 0       
            if formula.tape_python_compute:
                con_tape = safe_eval(formula.tape_python_compute, {'s': size, 'g': self.gap})
                if wastage_tape:
                    if wastage_tape.wastage>0:
                        con_tape += (con_tape*wastage_tape.wastage)/100
                self.tape_con = round(con_tape*self.product_uom_qty,4)

            if formula.wair_python_compute:
                con_wire = safe_eval(formula.wair_python_compute, {'s': size})
                if wastage_wire:
                    if wastage_wire.wastage>0:
                        con_wire += (con_wire*wastage_wire.wastage)/100
                self.wire_con = round(con_wire*self.product_uom_qty,4)
            if formula.slider_python_compute:
                con_slider = safe_eval(formula.slider_python_compute)
                if wastage_slider:
                    if wastage_slider.wastage>0:
                        con_slider += (con_slider*wastage_slider.wastage)/100
                self.slider_con = round(con_slider*self.product_uom_qty,4)
            if formula.twair_python_compute:
                con_top = safe_eval(formula.twair_python_compute)
                if wastage_top:
                    if wastage_top.wastage>0:
                        con_top += (con_top*wastage_top.wastage)/100
                self.topwire_con = round(con_top*self.product_uom_qty,4)
            if formula.bwire_python_compute:
                con_bottom = safe_eval(formula.bwire_python_compute)
                if wastage_bottom:
                    if wastage_bottom.wastage>0:
                        con_bottom += (con_bottom*wastage_bottom.wastage)/100
                self.botomwire_con = round(con_bottom*self.product_uom_qty,4)
            if formula.tbwire_python_compute:
                con_bottom = safe_eval(formula.tbwire_python_compute)
                if wastage_bottom:
                    if wastage_bottom.wastage>0:
                        con_bottom += (con_bottom*wastage_bottom.wastage)/100
                self.tbwire_con = round(con_bottom*self.product_uom_qty,4)
            if formula.pinbox_python_compute:
                con_pinbox = safe_eval(formula.pinbox_python_compute)
                if wastage_pinbox:
                    if wastage_pinbox.wastage>0:
                        con_pinbox += (con_pinbox*wastage_pinbox.wastage)/100
                self.pinbox_con = round(con_pinbox*self.product_uom_qty,4)

    def product_consumption(self,id):
        wastage_percent = self.env['wastage.percent']
        size_type = "inch"
        size = 0
        consumption = 0.0

        all_line = self.env['sale.order.line'].search([('order_id', '=', id)])
        if all_line:
            for line in all_line:
                if line.sizein == "N/A":
                    size_type = "cm"
                    size = line.sizecm
                else:
                    size = line.sizein
                if line.topbottom:
                    formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),('unit_type', '=', size_type),('topbottom_type', '=', line.topbottom)])
                else:
                    formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', line.product_id.product_tmpl_id.id),('unit_type', '=', size_type)])
                
                if formula:
                    tape_type = 'Cotton'
                    if line.dyedtape:
                        if tape_type in line.dyedtape:
                            wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Cotton Tape')])
                        else:
                            wastage_tape = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Tape')])
                    
                    else:
                        wastage_tape = False
        
                    wastage_slider = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Slider')])
                    wastage_top = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Top')])
                    wastage_bottom = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Bottom')])
                    wastage_wire = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Wire')])
                    wastage_pinbox = wastage_percent.search([('product_type', '=', formula.product_type),('material', '=', 'Pinbox')])
        
                    con_tape = con_wire = con_slider = con_top = con_bottom = con_pinboc = 0       
                    if formula.tape_python_compute:
                        con_tape = safe_eval(formula.tape_python_compute, {'s': size, 'g': line.gap})
                        if wastage_tape:
                            if wastage_tape.wastage>0:
                                con_tape += (con_tape*wastage_tape.wastage)/100
                        line.tape_con = round(con_tape*line.product_uom_qty,4)
        
                    if formula.wair_python_compute:
                        con_wire = safe_eval(formula.wair_python_compute, {'s': size})
                        if wastage_wire:
                            if wastage_wire.wastage>0:
                                con_wire += (con_wire*wastage_wire.wastage)/100
                        line.wire_con = round(con_wire*line.product_uom_qty,4)
                    if formula.slider_python_compute:
                        con_slider = safe_eval(formula.slider_python_compute)
                        if wastage_slider:
                            if wastage_slider.wastage>0:
                                con_slider += (con_slider*wastage_slider.wastage)/100
                        line.slider_con = round(con_slider*line.product_uom_qty,4)
                    if formula.twair_python_compute:
                        con_top = safe_eval(formula.twair_python_compute)
                        if wastage_top:
                            if wastage_top.wastage>0:
                                con_top += (con_top*wastage_top.wastage)/100
                        line.topwire_con = round(con_top*line.product_uom_qty,4)
                    if formula.bwire_python_compute:
                        con_bottom = safe_eval(formula.bwire_python_compute)
                        if wastage_bottom:
                            if wastage_bottom.wastage>0:
                                con_bottom += (con_bottom*wastage_bottom.wastage)/100
                        line.botomwire_con = round(con_bottom*line.product_uom_qty,4)
                    if formula.tbwire_python_compute:
                        con_bottom = safe_eval(formula.tbwire_python_compute)
                        if wastage_bottom:
                            if wastage_bottom.wastage>0:
                                con_bottom += (con_bottom*wastage_bottom.wastage)/100
                        line.tbwire_con = round(con_bottom*line.product_uom_qty,4)
                    if formula.pinbox_python_compute:
                        con_pinbox = safe_eval(formula.pinbox_python_compute)
                        if wastage_pinbox:
                            if wastage_pinbox.wastage>0:
                                con_pinbox += (con_pinbox*wastage_pinbox.wastage)/100
                        line.pinbox_con = round(con_pinbox*line.product_uom_qty,4)


        
