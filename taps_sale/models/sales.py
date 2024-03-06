# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _, exceptions
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import re
from decimal import Decimal, ROUND_HALF_UP
import decimal
from werkzeug.urls import url_encode
import logging
from odoo.tools.profiler import profile
from odoo.exceptions import RedirectWarning
import re

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = "sale.order"

    partner_id = fields.Many2one(
        'res.partner', string='Customer', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        required=False, change_default=True, index=True, tracking=1,
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_invoice_id = fields.Many2one(
        'res.partner', string='Invoice Address',
        readonly=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    partner_shipping_id = fields.Many2one(
        'res.partner', string='Delivery Address', readonly=True, required=False,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)], 'sale': [('readonly', False)]},
        domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]",)
    sample_type = fields.Selection([
        ('customer', 'Customer'),
        ('buyinghouse', 'Buying House'),
        ('pacc', 'Potential Account'),
    ],string="Sample Submission", required=True, default='customer')    
    provisionals_id = fields.Many2one(comodel_name='provisional.template', string='Provisional Acc')
    buying_house = fields.Many2one('res.partner', string='Buying House', domain="[('buying_house_rank', '>',0)]")
    user_id = fields.Many2one(
        'res.users', string='Salesperson',  default=False, required=True,
        domain="[('sale_team_id', '!=', False)]")
    # user_id = fields.Many2one(
    #     'res.users', string='Salesperson',)

    team_id = fields.Many2one(
        'crm.team', 'Sales Team', default=False, check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    
    region_id = fields.Many2one(
        'team.region', 'Region', default=False, check_company=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", readonly=True)
    
    priority_sales = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority Sales', default='0', index=True)
    buyer_type = fields.Selection([
            ('existing', 'Existing'),
            ('potential', 'Potential')],
            string='Type of Buyer', default='existing')
    buyer_name = fields.Many2one('res.partner', string='Buyer')
    provisionals_buyer = fields.Many2one('provisional.template', string='Provisional Buyer')
    season = fields.Char(string='Season')
    sample_ref = fields.Many2many(comodel_name='sale.order',
                                  relation='id_name',column1='id',column2='name',
                                  string='Sample Ref.', readonly=False, 
                                  domain=['|', ('sales_type', '=', 'sample'),('sales_type', '=', 'oldsa')])
    #sample_ref = fields.Many2many('sale.order', string='Sample Ref.', copy=False, states={'done': [('readonly', True)]})
    sales_type = fields.Selection([
            ('oldsa', 'Old Sample'),
            ('sample', 'Sample Order'),
            ('sale', 'Sales Order'),
            ('oldsale', 'OLD Sales Order'),
            ('oa', 'OA')],
            string='Sales Type', required=True)
    invoice_details = fields.Char(string='Invoice Details', related='partner_invoice_id.contact_address_complete')
    delivery_details = fields.Char(string='Delivery Details', readonly=True, related='partner_shipping_id.contact_address_complete')
    buying_house_delivery_details = fields.Char(string='BH Delivery Details', readonly=True, related='buying_house.contact_address_complete')
    # potential_delivery_details = fields.Char(string='PA Delivery Details', readonly=True, related='provisionals_id.contact_address_complete')
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
    order_ref = fields.Many2one('sale.order', string='Sales Order Ref.')
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
    sale_representative = fields.Many2one('sale.representative', string='Sales Representative', required=False, default=None)
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
            ('sample_pi', 'Sample PI'),
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
    usage = fields.Char(string='Usage')
    supply_chain = fields.Char(string='Supply Chain')
    priority = fields.Char(string="Priority")
    washing_type = fields.Selection([
        ('3HL40', '3HL40'),
        ('5HL40', '5HL40'),
        ('3HL60', '3HL60'),
        ('5HL60', '5HL60'),
        ('30HL40', '30HL40'),
        ('20HL40', '20HL40'),
        ('50HL40', '50HL40'),
        ('ENZYME WASH', 'ENZYME WASH')], string='Washing Type', default='3HL40')
    
    bcd_part_finish = fields.Char(string='B, C, D Part Finish')
    
    metal_detection = fields.Selection([
        ('N/A', 'N/A'),
        ('ϕ 1.0 m', 'ϕ 1.0 m'),
        ('ϕ 1.2 m', 'ϕ 1.2 m'),
        ('ϕ 1.5 m', 'ϕ 1.5 m'),
        ('ϕ 2.0 m', 'ϕ 2.0 m')],string='Metal Detection', default='ϕ 1.0 m')
    total_product_qty = fields.Float(string='Total PI Quantity' ,compute="_total_pi_quantity")
    sa_date = fields.Date(string='SA Date')
    pi_date = fields.Date(string='PI Date')
    old_sa_num = fields.Char(string='Old Sa Number')
    old_pi_num = fields.Char(string='Old PI Number')
    garments = fields.Char(string='Garments')
    corrosions_test = fields.Char(string='Corrosions Test Method')
    brand = fields.Char(string='Brand')
    closing_date = fields.Date(string='Closing Date')
    pr_delivery_date = fields.Date(string='Product Delivery Date')
    last_update_gsheet = fields.Datetime(string='Last Update GSheet')
    rmc = fields.Float(compute='_compute_rmc', string='RMC', store=True)
    earlier_ref = fields.Char(string='Earlier Ref')
    mockup_details = fields.Text(string= "Mockup Details")
    is_mockup_needed = fields.Boolean(string="mockup required", default=False)
    exp_close_date = fields.Date(string='Expected Closing Date')

    @api.onchange('sample_type')
    def _on_change_sample_type(self):
        self.partner_id = False
        self.buying_house= False
        self.provisionals_id = False

    @api.onchange('buyer_type')
    def _on_change_buyer_type(self):
        self.buyer_name = False
        self.provisionals_buyer= False

    

    @api.onchange('user_id')
    def compute_region_id(self):
        
        region = self.env['crm.team'].search([('id', '=', self.user_id.sale_team_id.region.id)], limit=1)
        # raise UserError((team))
        self.region_id= region.id

    @api.onchange('order_line')
    def onchange_mockup_update(self):
        for line in self.order_line:
            # raise UserError(('eiioi'))
            if "TIPPING" in line.product_template_id.name:
                self.is_mockup_needed= True
                break
            if "STOPPER" in line.product_template_id.name:
                self.is_mockup_needed= True
                break
            if "PRONG SNAP" in line.product_template_id.name:
                self.is_mockup_needed= True
                break
            if "BADGE" in line.product_template_id.name:
                self.is_mockup_needed= True
                break

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
                'user_id': False,
                
            })
            
            return

        self = self.with_company(self.company_id)

        addr = self.partner_id.address_get(['delivery', 'invoice'])
        partner_user = self.partner_id.user_id or self.partner_id.commercial_partner_id.user_id
        values = {
            'pricelist_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.id or False,
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
        }
        # user_id = partner_user.id
        # if not self.env.context.get('not_self_saleperson'):
        #     user_id = user_id or False
        # if user_id and self.user_id.id != user_id:
        #     values['user_id'] = user_id

        if self.env['ir.config_parameter'].sudo().get_param('account.use_invoice_terms') and self.env.company.invoice_terms:
            values['note'] = self.with_context(lang=self.partner_id.lang).env.company.invoice_terms
        # if not self.env.context.get('not_self_saleperson') or not self.team_id:
        #     values['team_id'] = self.env['crm.team'].with_context(
        #         default_team_id=self.partner_id.team_id.id
        #     )._get_default_team_id(domain=['|', ('company_id', '=', self.company_id.id), ('company_id', '=', False)], user_id=user_id)
        self.update(values)


    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        com_inv = self.env['combine.invoice'].search([('z_invoice','in', invoices.ids) or ('m_invoice','in', invoices.id)])
        # action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        action = self.env["ir.actions.actions"]._for_xml_id("taps_accounts.combine_invoice_action")
        if len(invoices) > 0:
            action['domain'] = [('id', '=', com_inv[0].id)]
        # elif len(invoices) == 1:
            form_view = [(self.env.ref('taps_accounts.combine_invoice_form_view').id, 'form')]
            # if 'views' in action:
            #     action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            # else:
            action['views'] = form_view
            action['res_id'] = com_inv[0].id
            # raise UserError(('invoices'))
        else:
            action = {'type': 'ir.actions.act_window_close'}
        return action

        # context = {
        #     'default_move_type': 'out_invoice',
        # }
        # if len(self) == 1:
        #     context.update({
        #         'default_partner_id': self.partner_id.id,
        #         'default_partner_shipping_id': self.partner_shipping_id.id,
        #         'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
        #         'default_invoice_origin': self.name,
        #     })
        # action['context'] = context

    

    def write(self, values):
        # return pickings_to_backorder.action_confirmation_wizard(show_transfers=self._should_show_transfers())
        state = self.state
        if 'is_hold' in values and self.state == "sale" and self.sales_type == "oa":
            # if values.get('is_hold'):
            operation = self.env['operation.details'].search([('oa_id','=', self.id)])
            if operation:
                mrp = self.env['manufacturing.order'].search([('oa_id','=', self.id)])
                op_update = operation.write({'state':'hold'})
                mrp_update = mrp.write({'state':'hold'})
        
        result = super(SaleOrder, self).write(values)
        if state == 'sale' and self.sales_type == 'oa':
            operation = self.env['operation.details'].search([('oa_id','=', self.id)])
            operation_pack = self.env['operation.packing'].search([('oa_id','=', self.id)])
            if operation or operation_pack:
                self.generate_m_order()
        return result

    def _compute_rmc(self):
        for rec in self:
            rec.rmc = round(sum(rec.mapped('order_line.rmc')),2)
        
    # def write(self, values):
    #     def confirm_callback():
    #         raise exceptions.UserError(('Confirmed!'))
    #     def cancel_callback():
    #         raise exceptions.UserError(('Cancelled!'))

    #     return {
    #         'type': 'ir.actions.client',
    #         'tag': 'confirmation_box',
    #         'name': 'confirmation',
    #         'params': {
    #             'title': 'Hold Confirmation',
    #             'subtitle': 'Are you sure you want to hold this order?',
    #             'confirm_callback': 'web.confirmation_boxes["confirmation"]._onClickConfirm',
    #             'cancel_callback': 'web.confirmation_boxes["confirmation"]._onClickCancel',
    #         }
    #     }
        
    #     result = super(SaleOrder, self).write(values)
    #     return result

    cancel_confirm = True
    def cancel_confirm (self, confirm = None):
        if confirm:
            cancel_warning = self._show_cancel_wizard()
            if cancel_warning:
                return {
                    'name': _('Cancel Sales Order'),
                    'view_mode': 'form',
                    'res_model': 'sale.order.cancel',
                    'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_order_id': self.id},
                    'target': 'new'
                }
            return self._action_cancel()
        
    def action_cancel(self):
        if self.state == "sale" and self.sales_type == "oa":
            mrp = self.env['operation.details'].search([('oa_id','=', self.id),('next_operation','=', 'FG Packing')])
            if mrp:
                return {
                    'name': _('Cancel Warning'),
                    'view_mode': 'form',
                    'res_model': 'oa.modification.confirmation',
                    'view_id': self.env.ref('taps_sale.view_modification_confirmation').id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_order_id': self.id},
                    'target': 'new'
                }
            else:
                cancel_warning = self._show_cancel_wizard()
                if cancel_warning:
                    return {
                        'name': _('Cancel Sales Order'),
                        'view_mode': 'form',
                        'res_model': 'sale.order.cancel',
                        'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
                        'type': 'ir.actions.act_window',
                        'context': {'default_order_id': self.id},
                        'target': 'new'
                    }
                return self._action_cancel()
        else:
            cancel_warning = self._show_cancel_wizard()
            if cancel_warning:
                return {
                    'name': _('Cancel Sales Order'),
                    'view_mode': 'form',
                    'res_model': 'sale.order.cancel',
                    'view_id': self.env.ref('sale.sale_order_cancel_view_form').id,
                    'type': 'ir.actions.act_window',
                    'context': {'default_order_id': self.id},
                    'target': 'new'
                }
            return self._action_cancel()


    
    @api.onchange('buyer_name')
    def buyer_name_change(self):
        if self.company_id.id == 1:
            self.hs_code= "9607.11.00"
        if self.company_id.id == 3:
            self.hs_code= "9606.22.00"
            if self.buyer_name.name == "RALPH LAUREN":
                self.brand = "POLO"
            
        # raise UserError((self.company_id.id))
        
        
    def action_copy(self):
        
        docs=self.env['sale.order.line'].search([('order_id','=', self.id),('is_selected', '=',True)])
        
        
        # raise UserError((doc_len))
        for record in docs:
            record.is_selected = False
            max_seq = max(line.sequence for line in self.order_line)
            # seq = record.sequence
            # raise UserError((seq))
            record.copy({'order_id': record.order_id.id,'sequence': max_seq+1})
            
            record.is_copied = True
            # return {'type': 'ir.actions.act_window_close'}

    def action_del(self):
        docs=self.env['sale.order.line'].search([('order_id','=', self.id),('is_selected', '=',True)])
        # raise UserError((docs))
        # max_seq = max(line.sequence for line in self.order_id.order_line)
        for record in docs:
            # record.is_selected = False
            record.unlink()
    def action_select_all(self):
        docs=self.env['sale.order.line'].search([('order_id','=', self.id)])
        for rec in docs:
            rec.is_selected = True
        
            
    # def action_send_card(self,id):
    #     template= self.env.ref('taps_sale.mail_template_oa_confirmation').id
    #     template = self.env['mail.template'].browse(template)
    #     template.send_mail(id, force_send=False)

    def _action_send_card(self,record):
        
        subject = record.company_id.name+ "(Ref " +(record.name)+")" or 'n/a)'
        body = 'Hello'
        # raise UserError((record.company_id.id))
        # report = self.env.ref('taps_sale.action_report_oa_invoice')
        if record.company_id.id == 1:
            report = self.env.ref('taps_sale.action_report_oa_invoice', False)
        if record.company_id.id == 3:
            report = self.env.ref('taps_sale.action_report_oa_invoice_mt', False)
        pdf_content, content_type = report.sudo()._render_qweb_pdf(record.id)
        attachment = self.env['ir.attachment'].sudo().create({
                    'name': record.name,
                    'type': 'binary',
                    'datas': base64.encodebytes(pdf_content),
                    'res_id': record.id
                })
        email_cc_list = [
            'alamgir@texzipperbd.com',
            'nitish.bassi@texzipperbd.com',
            'mirtunjoy.chatterjee@texzipperbd.com',
            record.sale_representative.leader.email,
            record.user_id.email_formatted or user.email_formatted
            ]
        if self.env.company.name == 'Zipper':
            email_cc_list.append('ranjeet.singh@texzipperbd.com')
            email_cc_list.append('csd.zipper@texzipperbd.com')
        if self.env.company.name == 'Metal Trims':
            email_cc_list.append('kumar.abhishek@texzipperbd.com')
            email_cc_list.append('nasir.csd@texzipperbd.com')
        if record.sale_representative.related_employee:
            email_cc_list.append(record.sale_representative.related_employee.parent_id.email)
        # raise UserError((email_cc_list))
        
        email_cc = ','.join(email_cc_list)
        
        mail_values = {
            'email_from':record.user_id.email_formatted or user.email_formatted,
            'author_id': self.env.user.partner_id.id,
            'model': None,
            'res_id': None,
            'subject': subject,
            'body_html': body,
            'auto_delete': True,
            'email_to': record.sale_representative.email,
            'attachment_ids': attachment,
            'email_cc': email_cc,
            
        }
        # raise UserError((mail_values['email_cc']))
        try:
            template = self.env.ref('taps_sale.email_template_for_confirm_oa', raise_if_not_found=True)
            
        except ValueError:
            _logger.warning('QWeb template mail.mail_notification_light not found when sending appraisal confirmed mails. Sending without layouting.')
        else:
            
            template_ctx = {
                'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name='OA')),
                'model_description': self.env['ir.model']._get('sale.order').display_name,
                'company': self.env.company,
                'record' : record,
            }
            # raise UserError((record.currency_id.symbol))
            body = template._render(template_ctx, engine='ir.qweb')
            mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            
        self.env['mail.mail'].sudo().create(mail_values).send()

        
    
    def _action_daily_oa_release_email(self, com_id):
        
        com = self.env['res.company'].search([('id', 'in', (com_id))])
        for rec in com: 
            subject = (rec.name)+' Unit Daily Released OA('+(datetime.now().strftime('%d %b, %Y'))+')'
            
            body = 'Hello'
            email_to_list = []
            email_to_list = [
                'mudit.tandon@texfasteners.com',
                'deepak.shah@bd.texfasteners.com',
                ]
            email_from_list = ['odoo@texzipperbd.com']
            email_cc_list = [
                'gaurav.gupta@bd.texfastener.com',
                'shahid.hossain@texzipperbd.com',
                'alamgir@texzipperbd.com',
                'nitish.bassi@texzipperbd.com',
                'suranjan.kumar@texzipperbd.com',
                'mirtunjoy.chatterjee@texzipperbd.com',
                'abdur.rahman@texzipperbd.com',
                'oa@bd.texfasteners.com',
                'costing@texzipperbd.com',
                'mis.mkt@texzipperbd.com',
                'asraful.haque@texzipperbd.com',
                ]
            author_id=0

            if rec.id == 1:
                report = rec.env.ref('taps_sale.action_report_daily_oa_release', False)
                email_cc_list.append('ranjeet.singh@texzipperbd.com')
                email_cc_list.append('csd.zipper@texzipperbd.com')
                # email_from_list.append('csd.zipper@texzipperbd.com')
            if rec.id == 3:
                report = rec.env.ref('taps_sale.action_report_daily_oa_release_mt', False)
                email_cc_list.append('kumar.abhishek@texzipperbd.com')
                email_cc_list.append('nasir.csd@texzipperbd.com')
                # email_from_list.append('nasir.csd@texzipperbd.com')
            pdf_content, content_type = report.sudo()._render_qweb_pdf()
            # author_list = ','.join(author_id)
            # raise UserError((pdf_content))
            attachment = rec.env['ir.attachment'].sudo().create({
                        'name': rec.name+' Daily OA Release('+(datetime.now().strftime('%d %b, %Y'))+')'+'.pdf',
                        'type': 'binary',
                        'datas': base64.encodebytes(pdf_content),
                        'mimetype': 'application/pdf',
                        'res_model' : 'sale.order',
                        'company_id' : rec.id,
            })
            email_cc = ','.join(email_cc_list)
            email_from = ','.join(email_from_list)
            email_to = ','.join(email_to_list)
            mail_values = {
                'email_from': email_from,
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': subject,
                'body_html': body,
                'auto_delete': True,
                'email_to': email_to,
                'email_cc': email_cc,
                'attachment_ids': attachment,
                'reply_to' : None,
                
            }
            # raise UserError((mail_values['author_id'],self.env.user.partner_id.id))
            try:
                
                template = rec.env.ref('taps_sale.view_oa_release_body', raise_if_not_found=True)
                
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending appraisal confirmed mails. Sending without layouting.')
            else:
                
                template_ctx = {
                    'message': rec.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name='OA.pdf')),
                    'model_description': rec.env['ir.model']._get('sale.order').display_name,
                    'company': rec,
                    'com' : rec,
                }
                
                body = template._render(template_ctx, engine='ir.qweb')
                # raise UserError((body))
                mail_values['body_html'] = rec.env['mail.render.mixin']._replace_local_links(body)
           
            rec.env['mail.mail'].sudo().create(mail_values).send()
    
    def _action_daily_oa_release_email_team_wise(self, team_id):
        
        team = self.env['crm.team'].search([('id', 'in', (team_id))])
        # raise UserError((team))
        for rec in team: 
            subject = (rec.name)+' Daily Released OA('+(datetime.now().strftime('%d %b, %Y'))+')'
            
            body = 'Hello'
            email_to_list = []
            email_to_list = []
            email_from_list = [
                'odoo@texzipperbd.com',
            ]
            email_cc_list = [
                # 'alamgir@texzipperbd.com',
                'asraful.haque@texzipperbd.com',
                'csd.zipper@texzipperbd.com',
                'nasir.csd@texzipperbd.com',
                ]
            author_id=0
            
            email_to_list.append(rec.user_id.login)
            email_cc_list.append(rec.core_leader.login)
                
    
            
            # raise UserError((ct['team_name']))
            report = rec.env.ref('taps_sale.action_report_daily_oa_release_team_wise', False)
            # report = report.with_context(ct)
            pdf_content, content_type = report.sudo()._render_qweb_pdf(res_ids=[rec.id], data={"team_id": rec.id})
            attachment = rec.env['ir.attachment'].sudo().create({
                        'name': rec.name+' Daily OA Release('+(datetime.now().strftime('%d %b, %Y'))+')'+'.pdf',
                        'type': 'binary',
                        'datas': base64.encodebytes(pdf_content),
                        'mimetype': 'application/pdf',
                        'res_model' : 'sale.order',
              
            })
            email_cc = ','.join(email_cc_list)
            email_from = ','.join(email_from_list)
            email_to = ','.join(email_to_list)
            mail_values = {
                'email_from': email_from,
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                'subject': subject,
                'body_html': body,
                'auto_delete': True,
                'email_to': email_to,
                'email_cc': email_cc,
                'attachment_ids' : attachment,
                'reply_to': None,
                
            }
            # raise UserError((rec.env.ref('taps_sale.view_oa_release_body_team_wise', raise_if_not_found=True)))
            try:
                
                template = rec.env.ref('taps_sale.view_oa_release_body_team_wise', raise_if_not_found=True)
                
            except ValueError:
                _logger.warning('QWeb template mail.mail_notification_light not found when sending appraisal confirmed mails. Sending without layouting.')
            else:
                
                template_ctx = {
                    'message': rec.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name='OA.pdf')),
                    'model_description': rec.env['ir.model']._get('sale.order').display_name,
                    'team' : rec,
                }
                
                    
                body = template._render(template_ctx, engine='ir.qweb')
                mail_values['body_html'] = rec.env['mail.render.mixin']._replace_local_links(body)
           
            rec.env['mail.mail'].sudo().create(mail_values).send()

    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        
        self.check_access_rights('read')
        povalue = 0
        # raise UserError(('hi'))
        result = {
            'regular': 0,#all_to_send
            'block': 0,#all_waiting
            'replacement': 0,#all_late
            
            'samplepi': 0,
            'sa': 0,
            'pi': 0,
            'oa': 0,
            'budget_value': 0,#all_avg_order_value
            'expense_value': 0,#all_avg_days_to_purchase
            'expense_percent': 0,#all_total_last_7_days
            'due_amount': 0,#all_sent_rfqs
            
        }

        currency = self.env.company.currency_id
        result['company'] = self.env.company.id
        current_datetime = datetime.now()


        first_date_of_current_month = current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_date_of_current_month = first_date_of_current_month + relativedelta(day=31)
        # raise UserError((first_date_of_current_month))
        so = self.env['sale.order']
        result['regular'] = so.search_count([('state', '=', 'sale'),('pi_type','=','regular')])
        
        result['replacement'] = so.search_count([('state', '=', 'sale'),('pi_type','=','replacement')])
        result['samplepi'] = so.search_count([('state', '=', 'sale'),('pi_type','=','samplepi')])
        result['sa'] = so.search_count([('state', '=', 'sale'),('sales_type','=','sample'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        result['pi'] = so.search_count([('state', '=', 'sale'),('sales_type','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        result['oa'] = so.search_count([('state', '=', 'sale'),('sales_type','=','oa'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])

        so = self.env['sale.order'].search([('sales_type','=','sale'),('state','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        result['pi_total'] = "{:.2f}".format(sum(so.mapped('total_product_qty')))
        result['pi_total_value'] ="{:.3f}".format(sum(so.mapped('amount_total'))/1000000)

        so = self.env['sale.order'].search([('sales_type','=','oa'),('state','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        result['oa_total'] = "{:.2f}".format(sum(so.mapped('total_product_qty')))
        result['oa_total_value'] ="{:.3f}".format(sum(so.mapped('amount_total'))/1000000)
        # raise UserError((result['company']))
        return result
    
    
    def _total_pi_quantity(self):
        for rec in self:
            rec.total_product_qty = sum(rec.order_line.mapped('product_uom_qty'))
    
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
                if line.sizemm:
                    if line.sizemm != 'N/A':
                        total_size += float(line.sizemm)
            rec.avg_size =(total_size/line_count)
    
    @api.onchange('order_ref')
    def _onchange_orderline_ids(self):
        if self.order_ref:
            self._create_oa()
        else:
            self.order_line = False #product_uom_qty
   
    @api.onchange('sample_ref')
    def _onchange_sample(self):
        if self.sample_ref:
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
                # 'payment_term_id': saleorder.payment_term_id.id,
                'partner_id': saleorder.order_ref.partner_id,
                'partner_invoice_id': saleorder.order_ref.partner_invoice_id,
                'partner_shipping_id': saleorder.order_ref.partner_shipping_id,
                'pricelist_id': saleorder.order_ref.pricelist_id,
                'currency_id': saleorder.order_ref.currency_id,
                # 'invoice_status': saleorder.order_ref.invoice_status,
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
                'usage' : saleorder.order_ref.usage,
                'supply_chain' : saleorder.order_ref.supply_chain,
                'priority' : saleorder.order_ref.priority,
                'washing_type' : saleorder.order_ref.washing_type,
                'metal_detection' : saleorder.order_ref.metal_detection,
                'bcd_part_finish' : saleorder.order_ref.bcd_part_finish,
                'garments' : saleorder.order_ref.garments,
                'corrosions_test' : saleorder.order_ref.corrosions_test,
                'bank': saleorder.order_ref.bank,
                'incoterm' : saleorder.order_ref.incoterm,
                'shipment_mode' : saleorder.order_ref.shipment_mode,
                'loading_place' : saleorder.order_ref.loading_place,
                'destination_port' : saleorder.order_ref.destination_port,
                'origin_country' : saleorder.order_ref.origin_country,
                'validity_period' : saleorder.order_ref.validity_period,
                'sale_representative' : saleorder.order_ref.sale_representative.id,
                'user_id' : saleorder.order_ref.user_id,
                'team_id' : saleorder.order_ref.team_id,
                'region_id' : saleorder.order_ref.region_id,
                'mockup_details' : saleorder.order_ref.mockup_details,
                
            })
            
            orderline = self.env['sale.order.line'].search([('order_id', '=', saleorder.order_ref.id)]).sorted(key = 'sequence')
            orderline_values = []
            for lines in orderline:
                orderline_values += [{
                    'order_id':self.id,
                    'name':lines.name,
                    'sequence':lines.sequence,
                    # 'invoice_lines':lines.invoice_lines,
                    # 'invoice_status':lines.invoice_status,
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
                    'qty_delivered':0,
                    'qty_delivered_manual':0,
                    'qty_to_invoice':0,
                    'qty_invoiced':0,
                    'untaxed_amount_invoiced':0,
                    'untaxed_amount_to_invoice':0,
                    'salesman_id':lines.salesman_id,
                    'currency_id':lines.currency_id,
                    'company_id':lines.company_id,
                    'order_partner_id':lines.order_partner_id,
                    # 'analytic_tag_ids':lines.analytic_tag_ids,
                    # 'analytic_line_ids':lines.analytic_line_ids,
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
                    'shade_name':lines.shade_name,
                    'shade_ref':lines.shade_ref,
                    'sizein':lines.sizein,
                    'sizecm':lines.sizecm,
                    'sizemm':lines.sizemm,
                    'logoref':lines.logoref,
                    'logo':lines.logo,
                    'logo_type':lines.logo_type,
                    'style':lines.style,
                    'gmt':lines.gmt,
                    'shapefin':lines.shapefin,
                    'bcdpart':lines.bcdpart,
                    'b_part':lines.b_part,
                    'c_part':lines.c_part,
                    'd_part':lines.d_part,
                    'back_part':lines.back_part,
                    'product_code':lines.product_code,
                    'shape':lines.shape,
                    'finish_ref':lines.finish_ref,
                    'dimension':lines.dimension,
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
                    'color' : lines.color,
                    'material_code' : lines.material_code,
                }]            
            
            #saleorder.order_ref.order_line#
            saleorder.order_line = [(5, 0)] + [(0, 0, value) for value in orderline_values]

            

    
    def _create_pi(self):
        for saleorder in self:
            # for saleorder in rec:
            #     if not saleorder.sample_ref:
            #         continue
            samp_len = len(saleorder.sample_ref)
            if samp_len == 1:
                saleorder.update({
                    'company_id': saleorder.sample_ref[0].company_id.id,
                    'date_order': saleorder.sample_ref[0].date_order,
                    'pi_date': saleorder.sample_ref[0].pi_date,
                    'validity_date': saleorder.sample_ref[0].validity_date,
                    'require_signature': saleorder.sample_ref[0].require_signature,
                    # 'require_payment': saleorder.sample_ref[0].require_payment,
                    'partner_id': saleorder.sample_ref[0].partner_id,
                    'partner_invoice_id': saleorder.sample_ref[0].partner_invoice_id,
                    'partner_shipping_id': saleorder.sample_ref[0].partner_shipping_id,
                    'pricelist_id': saleorder.sample_ref[0].pricelist_id,
                    'currency_id': saleorder.sample_ref[0].currency_id,
                    'invoice_status': saleorder.sample_ref[0].invoice_status,
                    'invoice_details': saleorder.sample_ref[0].invoice_details,
                    'delivery_details': saleorder.sample_ref[0].delivery_details,
                    'note' : saleorder.sample_ref[0].note,
                    # 'others_note': saleorder.sample_ref[0].others_note,
                    'remarks' : saleorder.sample_ref[0].remarks,
                    'kind_attention' : saleorder.sample_ref[0].kind_attention,
                    'customer_ref' : saleorder.sample_ref[0].customer_ref,
                    'style_ref' : saleorder.sample_ref[0].style_ref,
                    'season' : saleorder.sample_ref[0].season,
                    'department' : saleorder.sample_ref[0].department,
                    'division' : saleorder.sample_ref[0].division,
                    'buyer_name': saleorder.sample_ref[0].buyer_name,
                    'hs_code': saleorder.sample_ref[0].hs_code,
                    'production_type' : saleorder.sample_ref[0].production_type,
                    'production_group' : saleorder.sample_ref[0].production_group,
                    'order_type' : saleorder.sample_ref[0].order_type,
                    'usage' : saleorder.sample_ref[0].usage,
                    'supply_chain' : saleorder.sample_ref[0].supply_chain,
                    'priority' : saleorder.sample_ref[0].priority,
                    'washing_type' : saleorder.sample_ref[0].washing_type,
                    'metal_detection' : saleorder.sample_ref[0].metal_detection,
                    'bcd_part_finish' : saleorder.sample_ref[0].bcd_part_finish,
                    'garments' : saleorder.sample_ref[0].garments,
                    'corrosions_test' : saleorder.sample_ref[0].corrosions_test,
                    # 'po_no' : saleorder.sample_ref[0].po_no,
                    # 'po_date' : saleorder.sample_ref[0].po_date,
                    # 'revised_date' : saleorder.sample_ref[0].revised_date,
                    # 'dpi' : saleorder.sample_ref[0].dpi,
                    # 'bank': saleorder.sample_ref[0].bank,
                    'incoterm' : saleorder.sample_ref[0].incoterm,
                    'shipment_mode' : saleorder.sample_ref[0].shipment_mode,
                    'loading_place' : saleorder.sample_ref[0].loading_place,
                    'destination_port' : saleorder.sample_ref[0].destination_port,
                    'origin_country' : saleorder.sample_ref[0].origin_country,
                    'validity_period' : saleorder.sample_ref[0].validity_period,
                    'sale_representative' : saleorder.sample_ref[0].sale_representative.id,
                    'user_id' : saleorder.sample_ref[0].user_id,
                    'team_id' : saleorder.sample_ref[0].team_id,
                    'region_id' : saleorder.sample_ref[0].region_id,
                    'mockup_details' : saleorder.sample_ref[0].mockup_details,
                })
            
            orderline_values = []
            # samp_len = len(saleorder.sample_ref)
            # raise UserError((saleorder.sample_ref[0].id))
            sa_in = samp_len-1
            #for sample in saleorder.sample_ref:
            for re_lines in self.order_line:
                orderline_values += [{
                    'order_id':self.id,
                    'name':re_lines.name,
                    'sequence':re_lines.sequence,
                    'invoice_lines':re_lines.invoice_lines,
                    'invoice_status':re_lines.invoice_status,
                    'price_unit':re_lines.price_unit,
                    'price_subtotal':re_lines.price_subtotal,
                    'price_tax':re_lines.price_tax,
                    'price_total':re_lines.price_total,
                    'price_reduce':re_lines.price_reduce,
                    'tax_id':re_lines.tax_id,
                    'price_reduce_taxinc':re_lines.price_reduce_taxinc,
                    'price_reduce_taxexcl':re_lines.price_reduce_taxexcl,
                    'discount':re_lines.discount,
                    'product_id':re_lines.product_id,
                    'product_template_id':re_lines.product_template_id,
                    'product_updatable':re_lines.product_updatable,
                    'product_uom_qty':re_lines.product_uom_qty,
                    'product_uom':re_lines.product_uom,
                    'product_uom_category_id':re_lines.product_uom_category_id,
                    'product_uom_readonly':re_lines.product_uom_readonly,
                    'product_custom_attribute_value_ids':re_lines.product_custom_attribute_value_ids,
                    'product_no_variant_attribute_value_ids':re_lines.product_no_variant_attribute_value_ids,
                    'qty_delivered_method':re_lines.qty_delivered_method,
                    'qty_delivered':re_lines.qty_delivered,
                    'qty_delivered_manual':re_lines.qty_delivered_manual,
                    'qty_to_invoice':re_lines.qty_to_invoice,
                    'qty_invoiced':re_lines.qty_invoiced,
                    'untaxed_amount_invoiced':re_lines.untaxed_amount_invoiced,
                    'untaxed_amount_to_invoice':re_lines.untaxed_amount_to_invoice,
                    'salesman_id':re_lines.salesman_id,
                    'currency_id':re_lines.currency_id,
                    'company_id':re_lines.company_id,
                    'order_partner_id':re_lines.order_partner_id,
                    'analytic_tag_ids':re_lines.analytic_tag_ids,
                    'analytic_line_ids':re_lines.analytic_line_ids,
                    'is_expense':re_lines.is_expense,
                    'is_downpayment':re_lines.is_downpayment,
                    'state':re_lines.state,
                    'customer_lead':re_lines.customer_lead,
                    'display_type':re_lines.display_type,
                    'id':re_lines.id,
                    'display_name':re_lines.display_name,
                    'create_uid':re_lines.create_uid,
                    'create_date':re_lines.create_date,
                    'write_uid':re_lines.write_uid,
                    'write_date':re_lines.write_date,
                    'sale_order_option_ids':re_lines.sale_order_option_ids,
                    'product_packaging':re_lines.product_packaging,
                    'route_id':re_lines.route_id,
                    'move_ids':re_lines.move_ids,
                    'product_type':re_lines.product_type,
                    'virtual_available_at_date':re_lines.virtual_available_at_date,
                    'scheduled_date':re_lines.scheduled_date,
                    'forecast_expected_date':re_lines.forecast_expected_date,
                    'free_qty_today':re_lines.free_qty_today,
                    'qty_available_today':re_lines.qty_available_today,
                    'warehouse_id':re_lines.warehouse_id,
                    'qty_to_deliver':re_lines.qty_to_deliver,
                    'is_mto':re_lines.is_mto,
                    'display_qty_widget':re_lines.display_qty_widget,
                    'purchase_line_ids':re_lines.purchase_line_ids,
                    'purchase_line_count':re_lines.purchase_line_count,
                    'is_delivery':re_lines.is_delivery,
                    'product_qty':re_lines.product_qty,
                    'recompute_delivery_price':re_lines.recompute_delivery_price,
                    'is_configurable_product':re_lines.is_configurable_product,
                    'product_template_attribute_value_ids':re_lines.product_template_attribute_value_ids,
                    'topbottom':re_lines.topbottom,
                    'slidercode':re_lines.slidercode,
                    'finish':re_lines.finish,
                    'shade':re_lines.shade,
                    'sizein':re_lines.sizein,
                    'sizecm':re_lines.sizecm,
                    'sizemm':re_lines.sizemm,
                    'logoref':re_lines.logoref,
                    'logo':re_lines.logo,
                    'logo_type':re_lines.logo_type,
                    'style':re_lines.style,
                    'gmt':re_lines.gmt,
                    'shapefin':re_lines.shapefin,
                    'bcdpart':re_lines.bcdpart,
                    'b_part':re_lines.b_part,
                    'c_part':re_lines.c_part,
                    'd_part':re_lines.d_part,
                    'back_part':re_lines.back_part,
                    'product_code':re_lines.product_code,
                    'shape':re_lines.shape,
                    'finish_ref':re_lines.finish_ref,
                    'nailmat':re_lines.nailmat,
                    'nailcap':re_lines.nailcap,
                    'fnamebcd':re_lines.fnamebcd,
                    'nu1washer':re_lines.nu1washer,
                    'nu2washer':re_lines.nu2washer,
                    'slidercodesfg':re_lines.slidercodesfg,
                    'dyedtape':re_lines.dyedtape,
                    'ptopfinish':re_lines.ptopfinish,
                    'numberoftop':re_lines.numberoftop,
                    'pbotomfinish':re_lines.pbotomfinish,
                    'ppinboxfinish':re_lines.ppinboxfinish,
                    'dippingfinish':re_lines.dippingfinish,
                    'gap':re_lines.gap,
                    'bom_id':re_lines.bom_id,
                    'tape_con':re_lines.tape_con,
                    'slider_con':re_lines.slider_con,
                    'topwire_con':re_lines.topwire_con,
                    'botomwire_con':re_lines.botomwire_con,
                    'wire_con':re_lines.wire_con,
                    'pinbox_con':re_lines.pinbox_con,
                    'dimension' : re_lines.dimension,
                    
        
                }]

            
            orderline = self.env['sale.order.line'].search([('order_id.name', '=', saleorder.sample_ref[sa_in].name)]).sorted(key = 'sequence')
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
                    'style':lines.style,
                    'gmt':lines.gmt,
                    'shapefin':lines.shapefin,
                    'bcdpart':lines.bcdpart,
                    'b_part':lines.b_part,
                    'c_part':lines.c_part,
                    'd_part':lines.d_part,
                    'back_part':lines.back_part,
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
                    'dimension' : lines.dimension,
                    'material_code':lines.material_code,
                    
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



    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())
        #bom = self.env['mrp.bom']
        #--------- BOM Start -----------#

        #--------- BOM End -------------#

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        
        context = self._context.copy()
        context.pop('default_name', None)
        
        # if self.sales_type == 'oa':
        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        if self.sales_type == 'oa':
            self.order_line.product_consumption(self.id)
            self.order_line.compute_shadewise_tape()
            self.generate_m_order()
        return True
        

    def generate_m_order(self):
        exist_mrp = self.env['manufacturing.order'].search([('oa_id','=',self.id),('company_id','=',self.company_id.id)])
        operation = self.env['operation.packing'].search([('oa_id','=',self.id),('company_id','=',self.company_id.id)])
        w_centers = self.env['mrp.workcenter'].search([('company_id','=',self.company_id.id),('name','=','Packing')])
        w_center = w_centers.id
        for products in self.order_line:
            # sale_line_of_top
            # COIL 3 SLIDER, COIL 5 SLIDER
            can_create = True
            op_can_create = True
            mrp_lines = None
            sale_lines = None
            mrp_id = None
            qty = 0
            state = 'waiting'
            if self.is_hold:
                state = 'hold'
            if self.state == 'cancel':
                state = 'cancel'
            if state != 'cancel':
                if products.product_id.product_tmpl_id.name in ('METAL 5 SLIDER','METAL 4 SLIDER'):
                    if products.numberoftop:
                        num_of_top = 1
                        if products.numberoftop == 'Double':
                            num_of_top = 2
                        top = exist_mrp.filtered(lambda mo: mo.sale_line_of_top == products.id)
                        top_ope = operation.filtered(lambda mo: mo.sale_line_of_top == products.id)
                        qty = products.product_uom_qty * num_of_top
                        product_all = self.env['product.product'].browse(129294)
                        get_top = self.env['sale.order.option'].sudo().search([('order_id','=',self.id),('line_id','=',products.id)])
                        create_top_line = get_top
                        if get_top:
                            ope_top_update = get_top.sudo().update({'quantity':qty})
                        else:
                            create_top_line = self.env['sale.order.option'].create({
                                'order_id':self.id,
                                'line_id':products.id,
                                'name':product_all.product_tmpl_id.display_name,
                                'product_id':product_all.id,   'price_unit':0,
                                'discount':0,
                                'uom_id':product_all.product_tmpl_id.uom_id.id,
                                'quantity':qty,
                                'sequence':products.sequence})
                            
                            ope = self.env['operation.packing.topbottom'].create({'name':'',
                                                            'sale_order_option':create_top_line.id,
                                                            'action_date':self.date_order,
                                                            'state':state,
                                                            })
                        
            if exist_mrp:
                if exist_mrp[0].state == 'closed':
                    state = 'closed'
                m_order = exist_mrp.filtered(lambda mo: mo.sale_order_line.id == products.id)
                if m_order:
                    can_create = False
                    oa_tot_done = 0
                    oa_tot_done = m_order[0].oa_total_qty - m_order[0].oa_total_balance
                    mrp_update = m_order.update({'topbottom':products.topbottom,'slidercodesfg':products.slidercodesfg,'finish':products.finish,'shade':products.shade,'shade_ref':products.shade,'sizein':products.sizein,'sizecm':products.sizecm,'sizemm':products.sizemm,'dyedtape':products.dyedtape,'ptopfinish':products.ptopfinish,'numberoftop':products.numberoftop,'pbotomfinish':products.pbotomfinish,'ppinboxfinish':products.ppinboxfinish,'dippingfinish':products.dippingfinish,'gap':products.gap,'oa_total_qty':products.order_id.total_product_qty + qty,'oa_total_balance':((products.order_id.total_product_qty + qty) - oa_tot_done), 'remarks':products.order_id.remarks,'revision_no':self.revised_no,'logo':products.logo,'logoref':products.logoref,'logo_type':products.logo_type,'style':products.style,'gmt':products.gmt,'shapefin':products.shapefin,'b_part':products.b_part,'c_part':products.c_part,'d_part':products.d_part,'finish_ref':products.finish_ref,'product_code':products.product_code,'shape':products.shape,'back_part':products.back_part,'state':state})
                    mrp_lines = str(m_order.id)
                    sale_lines = str(products.id)
                    mrp_id = m_order.id
            if operation:
                op = operation.filtered(lambda mo: mo.sale_order_line.id == products.id)
                if op:
                    op_can_create = False
            
            if can_create == True:
                mrp_ = self.env['manufacturing.order'].create({'sale_order_line':products.id,'oa_id':products.order_id.id,'company_id':products.order_id.company_id.id,'buyer_name':products.order_id.buyer_name.name,'topbottom':products.topbottom,'slidercodesfg':products.slidercodesfg,'finish':products.finish,'shade':products.shade,'shade_ref':products.shade,'sizein':products.sizein,'sizecm':products.sizecm,'sizemm':products.sizemm,'dyedtape':products.dyedtape,'ptopfinish':products.ptopfinish,'numberoftop':products.numberoftop,'pbotomfinish':products.pbotomfinish,'ppinboxfinish':products.ppinboxfinish,'dippingfinish':products.dippingfinish,'gap':products.gap,'oa_total_qty':products.order_id.total_product_qty + qty,'oa_total_balance':products.order_id.total_product_qty + qty,'remarks':products.order_id.remarks,'state':state,'revision_no':self.revised_no,'logo':products.logo,'logoref':products.logoref,'logo_type':products.logo_type,'style':products.style,'gmt':products.gmt,'shapefin':products.shapefin,'b_part':products.b_part,'c_part':products.c_part,'d_part':products.d_part,'finish_ref':products.finish_ref,'product_code':products.product_code,'shape':products.shape,'back_part':products.back_part})
                
                mrp_lines = str(mrp_.id)
                sale_lines = str(products.id)
                mrp_id = mrp_.id
            if op_can_create == True:
                ope = self.env['operation.packing'].create({'name':'',
                                                            'mrp_line':mrp_id,
                                                            'sale_order_line':products.id,
                                                            'action_date':self.date_order,
                                                            'qty':0,
                                                            'state':state,
                                                            })

        if state != 'cancel':
            current_mrp = self.env['manufacturing.order'].search([('oa_id','=',self.id),('company_id','=',self.company_id.id)])
            e_operation = self.env['operation.packing'].search([('oa_id','=',self.id),('done_qty','=',0)])
    
            delete_operation = e_operation.filtered(lambda sol: sol.sale_order_line == True and sol.sale_order_line not in current_mrp.sale_order_line.ids)
            
            delete_top_operation = e_operation.filtered(lambda sol: sol.sale_line_of_top == True and sol.sale_line_of_top not in current_mrp.sale_order_line.ids)
            
            if delete_operation:
                delete_operation.unlik()
            if delete_top_operation:
                delete_top_operation.unlik()
        
    # def manuf_values(self,seq,id,oa,company):
    #     values = 
    #     return values
        
    def mrp_values(self,id,product,qty,uom,bom,shade,finish,sizein,sizecm):
        if sizein == 'N/A':
            sizein = ''
        if sizecm == 'N/A':
            sizecm = ''
        
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
            'sale_order_line':id,
            'shade':shade,
            'finish':finish,
            'sizein':sizein,
            'sizecm':sizecm
        }
        return values
        
    def generate_mrp(self):
        unique_shade = []
        unique_slider = []
        unique_top = []
        unique_bottom = []
        for products in self.order_line:
            mrp_production = self.env['mrp.production'].create(self.mrp_values(products.id,products.product_id.id,products.product_qty,products.product_uom.id,products.bom_id,products.shade,products.finish,products.sizein,products.sizecm))
            mrp_production.move_raw_ids.create(mrp_production._get_moves_raw_values())
            mrp_production._onchange_workorder_ids()
            mrp_production._create_update_move_finished()
            bom_lines = self.env['mrp.bom.line'].search([('bom_id','=',products.bom_id)])
            #raise UserError((products.bom_id))
            for lines in bom_lines:
                bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', lines.product_id.product_tmpl_id.id)])
                if 'Slider' in lines.product_id.product_tmpl_id.name:
                    filtered_slider = [x for x in unique_slider 
                                       if x[0] == products.product_id.product_tmpl_id.id 
                                       and x[1] == products.slidercodesfg and x[2] == products.finish]
                    if not filtered_slider:
                        same_slider = self.order_line.filtered(lambda sol: sol.product_id.product_tmpl_id.id == products.product_id.product_tmpl_id.id and sol.slidercodesfg == products.slidercodesfg and sol.finish == products.finish)
                        product_qty = sum(same_slider.mapped('product_qty'))
                        qty = (lines.product_qty/100) * product_qty
                        mrp_sl_production = self.env['mrp.production'].create(self.mrp_values(products.id,lines.product_id.id,qty,lines.product_uom_id.id,bom.id,'',products.finish,'',''))
                        mrp_sl_production.move_raw_ids.create(mrp_sl_production._get_moves_raw_values())
                        mrp_sl_production._onchange_workorder_ids()
                        mrp_sl_production._create_update_move_finished()
                        _slider = []
                        _slider = [products.product_id.product_tmpl_id.id,products.slidercodesfg,products.finish]
                        unique_slider.append(_slider)
                elif 'Plated Top' in lines.product_id.product_tmpl_id.name:
                    filtered_top = [x for x in unique_top
                                       if x[0] == products.product_id.product_tmpl_id.id 
                                       and x[1] == products.ptopfinish and x[2] == products.finish]
                    if not filtered_top:
                        same_top = self.order_line.filtered(lambda sol: sol.product_id.product_tmpl_id.id == products.product_id.product_tmpl_id.id and sol.ptopfinish == products.ptopfinish and sol.finish == products.finish)
                        product_qty = sum(same_top.mapped('product_qty'))
                        qty = (lines.product_qty/100) * product_qty
                        mrp_top_production = self.env['mrp.production'].create(self.mrp_values(products.id,lines.product_id.id,qty,lines.product_uom_id.id,bom.id,'',products.finish,'',''))
                        mrp_top_production.move_raw_ids.create(mrp_top_production._get_moves_raw_values())
                        mrp_top_production._onchange_workorder_ids()
                        mrp_top_production._create_update_move_finished()
                        _top = []
                        _top = [products.product_id.product_tmpl_id.id,products.ptopfinish,products.finish]
                        unique_top.append(_top)
                elif 'Plated Bottom' in lines.product_id.product_tmpl_id.name:
                    filtered_bottom = [x for x in unique_bottom 
                                       if x[0] == products.product_id.product_tmpl_id.id 
                                       and x[1] == products.pbotomfinish and x[2] == products.finish]
                    if not filtered_bottom:
                        same_bottom = self.order_line.filtered(lambda sol: sol.product_id.product_tmpl_id.id == products.product_id.product_tmpl_id.id and sol.pbotomfinish == products.pbotomfinish and sol.finish == products.finish)
                        product_qty = sum(same_bottom.mapped('product_qty'))
                        qty = (lines.product_qty/100) * product_qty
                        mrp_bottom_production = self.env['mrp.production'].create(self.mrp_values(products.id,lines.product_id.id,qty,lines.product_uom_id.id,bom.id,'',products.finish,'',''))
                        mrp_bottom_production.move_raw_ids.create(mrp_bottom_production._get_moves_raw_values())
                        mrp_bottom_production._onchange_workorder_ids()
                        mrp_bottom_production._create_update_move_finished()
                        _bottom = []
                        _bottom = [products.product_id.product_tmpl_id.id,products.pbotomfinish,products.finish]
                        unique_bottom.append(_bottom)
                else:
                    qty = (lines.product_qty/100) * products.product_qty
                    mrp_sf_production = self.env['mrp.production'].create(self.mrp_values(products.id,lines.product_id.id,qty,lines.product_uom_id.id,bom.id,products.shade,products.finish,products.sizein,products.sizecm))
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
                        
                        filtered_shade = [x for x in unique_shade if x[0] == products.product_id.product_tmpl_id.id and x[1] == products.dyedtape and x[2] == products.shade]
                        if filtered_shade:
                            #raise UserError((filtered_shade,'sdfdf'))
                            a = 'a'
                        else:
                            #raise UserError((filtered_shade))
                            same_shade = self.order_line.filtered(lambda sol: sol.product_id.product_tmpl_id.id == products.product_id.product_tmpl_id.id and sol.dyedtape == products.dyedtape and sol.shade == products.shade)
                            product_qty = sum(same_shade.mapped('product_qty'))
                            #raise UserError(((sub_lines.product_qty/100),product_qty))
                            sub_qty = (sub_lines.product_qty/100) * product_qty

                            sub_production = self.env['mrp.production'].create(self.mrp_values(products.id,sub_lines.product_id.id,sub_qty,sub_lines.product_uom_id.id,sub_bom.id,products.shade,'','',''))
                            sub_production.move_raw_ids.create(sub_production._get_moves_raw_values())
                            sub_production._onchange_workorder_ids()
                            sub_production._create_update_move_finished()
                            #sub_production.action_confirm()
                            
                        _shade = []
                        _shade = [products.product_id.product_tmpl_id.id,products.dyedtape,products.shade]
                        unique_shade.append(_shade)
                        
                #mrp_sf_production.action_confirm()
            #mrp_production.action_confirm()
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
                
            if vals.get('sales_type') == "oldsa":
                ref = self.env['ir.sequence'].next_by_code('', sequence_date=seq_date) or _(vals['old_sa_num'])
                vals['name'] = ref
                # raise UserError((vals['name']))
            if vals.get('sales_type') == "oldsale":
                ref = self.env['ir.sequence'].next_by_code('', sequence_date=seq_date) or _(vals['old_pi_num'])
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
                order_ref = self.env['sale.order'].sudo().search([('id', '=' , vals.get('order_ref'))])
                vals['payment_term_id'] = order_ref.payment_term_id.id
                
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
    # def unlink(self):
    #     for order in self:
    #         if order.state not in ('draft', 'cancel'):
    #             raise UserError(_('You can not delete a sent quotation or a confirmed sales order. You must first cancel it.'))
    #     return super(SaleOrder, self).unlink()
    
class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    topbottom = fields.Text(string='Top/Bottom', store=True)
    slidercode = fields.Text(string='Slider Code', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    shade_name = fields.Text(string='Full Shade', store=True)
    shade_ref = fields.Text(string='Shade Ref', store=True)
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
    style = fields.Text(string='Style', store=True)
    gmt = fields.Text(string='Gmt', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    b_part = fields.Text(string='B Part', store=True)
    c_part = fields.Text(string='C Part', store=True)
    d_part = fields.Text(string='D Part', store=True)
    finish_ref = fields.Text(string='Finish Ref', store=True)
    product_code = fields.Text(string='Product Code', compute='_compute_product_code',inverse='_inverse_compute_product_code',store=True)
    shape = fields.Text(string='Shape', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    back_part = fields.Text(string='Back Part', store=True)
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
    dimension = fields.Char(string='Dimension')
    line_code = fields.Char(string='Line Code', compute="_compute_line_code")
    mold_set = fields.Char(string='Mold Set')
    weight_per_gross = fields.Float(string='Weight/Gross', compute='_compute_weight_per_gross', inverse='_inverse_compute_weight_per_gross', store=True)
    is_selected = fields.Boolean('Select',default=False)
    is_copied = fields.Boolean('Copied',default=False)
    last_update_gsheet = fields.Datetime(string='Last Update GSheet')
    rmc = fields.Float(string='RMC', store=True)
    sale_line_of_top = fields.Integer(string='Sale Line of Top', store=True, readonly=True)
    material_code = fields.Char(string="Material Code")
    
    def _inverse_compute_product_code(self):
        pass

    def _inverse_compute_weight_per_gross(self):
        pass
        
    @api.depends('product_template_id','sizemm','product_uom_qty')
    def _compute_weight_per_gross(self):
        for rec in self:
            if rec.product_template_id:
                if 'SHANK' in rec.product_template_id.name and 'HOLE SHANK' not in rec.product_template_id.name:
                    if rec.sizemm == '17':
                        rec.weight_per_gross = (.24*rec.product_uom_qty)
                    elif rec.sizemm == '18':
                        rec.weight_per_gross = (.27*rec.product_uom_qty)
                    elif rec.sizemm == '19':
                        rec.weight_per_gross = (.30*rec.product_uom_qty)
                    elif rec.sizemm == '20':
                        rec.weight_per_gross = (.32*rec.product_uom_qty)
                    else:
                        rec.weight_per_gross = 0.0
                elif 'HOLE SHANK' in rec.product_template_id.name:
                    if rec.sizemm == '17':
                        rec.weight_per_gross = (.24*rec.product_uom_qty)
                    elif rec.sizemm == '18':
                        rec.weight_per_gross = (.26*rec.product_uom_qty)
                    elif rec.sizemm == '19':
                        rec.weight_per_gross = (.38*rec.product_uom_qty)
                    elif rec.sizemm == '20':
                        rec.weight_per_gross = (.30*rec.product_uom_qty)
                    else:
                        rec.weight_per_gross = 0.0

                elif 'SNAP' in rec.product_template_id.name:
                    if rec.sizemm == '10':
                        rec.weight_per_gross = (.28*rec.product_uom_qty)
                    elif rec.sizemm == '12' or rec.sizemm == '13':
                        rec.weight_per_gross = (.33*rec.product_uom_qty)
                    elif rec.sizemm == '14':
                        rec.weight_per_gross = (.36*rec.product_uom_qty)
                    elif rec.sizemm == '15':
                        rec.weight_per_gross = (.37*rec.product_uom_qty)
                    elif rec.sizemm == '17':
                        rec.weight_per_gross = (.39*rec.product_uom_qty)
                    elif rec.sizemm == '18':
                        rec.weight_per_gross = (.430*rec.product_uom_qty)
                    else:
                        rec.weight_per_gross = 0.0

                elif 'EYELET' in rec.product_template_id.name:
                    if rec.sizemm == '9':
                        rec.weight_per_gross = (.052*rec.product_uom_qty)
                    elif rec.sizemm == '10':
                        rec.weight_per_gross = (.054*rec.product_uom_qty)
                    elif rec.sizemm == '11':
                        rec.weight_per_gross = (.057*rec.product_uom_qty)
                    elif rec.sizemm == '12':
                        rec.weight_per_gross = (.062*rec.product_uom_qty)
                    elif rec.sizemm == '13':
                        rec.weight_per_gross = (.067*rec.product_uom_qty)
                    elif rec.sizemm == '14':
                        rec.weight_per_gross = (.090*rec.product_uom_qty)
                    elif rec.sizemm == '15':
                        rec.weight_per_gross = (.100*rec.product_uom_qty)
                    elif rec.sizemm == '16':
                        rec.weight_per_gross = (.110*rec.product_uom_qty)
                    elif rec.sizemm == '20':
                        rec.weight_per_gross = (.180*rec.product_uom_qty)
                    else:
                        rec.weight_per_gross = 0.0

                elif 'RIVET' in rec.product_template_id.name:
                    if rec.sizemm == '6':
                        rec.weight_per_gross = (.065*rec.product_uom_qty)
                    elif rec.sizemm == '7':
                        rec.weight_per_gross = (.072*rec.product_uom_qty)
                    elif rec.sizemm == '8':
                        rec.weight_per_gross = (.080*rec.product_uom_qty)
                    elif rec.sizemm == '9':
                        rec.weight_per_gross = (.090*rec.product_uom_qty)
                    elif rec.sizemm == '10':
                        rec.weight_per_gross = (.095*rec.product_uom_qty)
                    else:
                        rec.weight_per_gross = 0.0
                
                else:
                    rec.weight_per_gross = 0.0
                
    
    
    @api.depends('product_template_id','back_part','sizemm','dimension')
    def _compute_product_code(self):
        for rec in self:
            if rec.product_template_id and "EYELET" not in rec.product_template_id.name:
                if rec.product_template_id:
                    rec.product_code =''.join([word[0] for word in rec.product_template_id.name.split()])
                if rec.sizemm:
                    rec.product_code =rec.product_code+"-"+str(rec.sizemm)
                if rec.back_part:
                    if rec.back_part == "2 PIN SHANK":
                        rec.product_code =rec.product_code+"-"+''.join("2SB")
                    if rec.back_part == "N/A":
                        rec.product_code =rec.product_code+"-"+''.join("XX")
                    if rec.back_part == "SS SHANK":
                        rec.product_code =rec.product_code+"-"+''.join("SS")
                    if rec.back_part == "BRASS SHANK" or rec.back_part == "BRASS EYELET":
                        rec.product_code =rec.product_code+"-"+''.join("BR")
                    if rec.back_part == "MOVING SHANK":
                        rec.product_code =rec.product_code+"-"+''.join("MS")
                    if rec.back_part == "NYLON SHANK":
                        rec.product_code =rec.product_code+"-"+''.join("NY")
                    if rec.back_part == "ALUMINIUM SHANK":
                        rec.product_code =rec.product_code+"-"+''.join("AL")
                if rec.dimension:
                    rec.product_code = rec.product_code+"-"+str(rec.dimension)

            elif rec.product_template_id and "EYELET"  in rec.product_template_id.name:
                if rec.sizemm == '8':
                    rec.product_code = "E4.0-8.0"
                elif rec.sizemm == '9':
                    rec.product_code = "E5.0-9.0"
                elif rec.sizemm == '9.5':
                    rec.product_code = "E5.0-9.5"
                elif rec.sizemm == '10':
                    rec.product_code = "E5.0-10.0"
                elif rec.sizemm == '10.5':
                    rec.product_code = "E5.0-11.0"
                elif rec.sizemm == '11':
                    rec.product_code = "E5.0-11.0/E6.0-11.0"
                elif rec.sizemm == '11.5':
                    rec.product_code = "E7.0-11.5/E6.0-11.5"
                elif rec.sizemm == '12':
                    rec.product_code = "E6.0-12.0/E7.0-12.0"
                elif rec.sizemm == '12.5':
                    rec.product_code = "E7.0-12.5"
                elif rec.sizemm == '13':
                    rec.product_code = "E7.0-13.0"
                elif rec.sizemm == '14':
                    rec.product_code = "E8.0-14.0"
                elif rec.sizemm == '15':
                    rec.product_code = "E8.0-15.0"
                elif rec.sizemm == '16':
                    rec.product_code = "E10.0-16.0"
                elif rec.sizemm == '17':
                    rec.product_code = "E9.0-17.0"
                elif rec.sizemm == '18':
                    rec.product_code = "E12.0-18.0"
                elif rec.sizemm == '19':
                    rec.product_code = "E12.0-19.0"
                elif rec.sizemm == '20':
                    rec.product_code = "E12.0-20.0/E9.0-20.0"
                elif rec.sizemm == '21':
                    rec.product_code = "E12.0-21.0"
                elif rec.sizemm == '22':
                    rec.product_code = "E14.0-22.0/E12.0-22.0"
                elif rec.sizemm == '25':
                    rec.product_code = "E14.0-25.0"
                elif rec.sizemm == '33.5':
                    rec.product_code = "E20.0-33.5"
                else:
                    rec.product_code = ""
                
                
            
        

    def _compute_line_code(self):
        count = 0
        for rec in self:
            count += 1
            rec.line_code = rec.order_id.name +"_0"+str(count)
    
  
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
    
    # def duplicate_line(self):
    #     max_seq = max(line.sequence for line in self.order_id.order_line)
    #     orderline_values = []
        
    #     orderline_values.append((0, 0, {
    #         'name':self.name,
    #         'sequence':max_seq,
    #         'price_unit':self.price_unit,
    #         'price_subtotal':self.price_subtotal,
    #         'price_tax':self.price_tax,
    #         'price_total':self.price_total,
    #         'price_reduce':self.price_reduce,
    #         'tax_id':self.tax_id,
    #         'price_reduce_taxinc':self.price_reduce_taxinc,
    #         'price_reduce_taxexcl':self.price_reduce_taxexcl,
    #         'discount':self.discount,
    #         'product_id':self.product_id.id,
    #         'product_template_id':self.product_template_id,
    #         'product_updatable':self.product_updatable,
    #         'product_uom_qty':self.product_uom_qty,
    #         'product_uom':self.product_uom.id,
    #         'product_uom_category_id':self.product_uom_category_id,
    #         'product_uom_readonly':self.product_uom_readonly,
    #         'currency_id':self.currency_id.id,
    #         'company_id':self.company_id.id,
    #         'display_type':self.display_type,
    #         'display_name':self.display_name,
    #         'create_uid':self.create_uid.id,
    #         'create_date':self.create_date,
    #         'write_uid':self.write_uid.id,
    #         'write_date':self.write_date,
    #         'product_type':self.product_type,
    #         'product_qty':self.product_qty,
    #         'sizecm':self.sizecm,
    #         'sizein':self.sizein,
    #         'gap':self.gap,
    #         'topbottom':self.topbottom,
    #     }))
    #     self.order_id.update({'order_line': orderline_values,})
    
        
    @api.onchange('product_id')
    def product_id_change(self):
        # raise UserError((self))
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
        #raise UserError((atv))
        for rec in atv:
            # if rec.attribute_id.name == 'Size (Inch)':
            #     name = rec.product_attribute_value_id.name
            #     custom_values = self.product_custom_attribute_value_ids.filtered(lambda p: p.custom_product_template_attribute_value_id.id == rec.id)
            #     if custom_values.custom_value:
            #         raise UserError((custom_values.custom_value))
            #         name += "\n" + custom_values.custom_value
            #         self.shade = name
                    
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
            if rec.attribute_id.name == 'Dimension':
                self.dimension = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Style':
                self.style = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Usage':
                self.usage = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Supply Chain':
                self.supply_chain = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Gmt':
                self.gmt = rec.product_attribute_value_id.name
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
            if rec.attribute_id.name == 'Back Part':
                self.back_part = rec.product_attribute_value_id.name
                continue
            # if rec.attribute_id.name == 'Product Code':
            #     self.product_code = rec.product_attribute_value_id.name
            #     continue
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
            if rec.attribute_id.name == 'Material Code':
                self.material_code = rec.product_attribute_value_id.name
                continue
        if self.product_template_id.name == 'SHANK BUTTON 100213086':
            self.logo='WAVY POLO'
            self.logoref='T-5252'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100213083':
            self.logo='WAVY POLO'
            self.logoref='T-5252'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'HOLE SHANK BUTTON 100212195':
            self.logo='WREATH'
            self.logoref='D-785'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100212194':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100214452':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'SNAP BUTTON 100214456':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'HOLE SHANK BUTTON 100214448':
            self.logo='WREATH'
            self.logoref='D-785'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'SNAP BUTTON 100214444':
            self.logo='LAUREL WREATH'
            self.logoref='D-786'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'SNAP BUTTON 100214449':
            self.logo='WAVY POLO'
            self.logoref='T-5252'
            self.finish_ref='TS-411703'
        elif self.product_template_id.name == 'SNAP BUTTON 100214445':
            self.logo='LAUREL WREATH'
            self.logoref='D-786'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100214454':
            self.logo='WORK-WEAR'
            self.logoref = 'T-4998'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100214447':
            self.logo='WAVY POLO R.LAUREN'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100217521':
            self.logo='WAVY POLO'
            self.logoref='T-5252'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100217522':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100217662':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100217762':
            self.logo='CLASSIC POLO RALPH LAUREN'
            self.logoref='D-786'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SHANK BUTTON 100217763':
            self.logo='WREATH'
            self.logoref='D-785'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100217792':
            self.logo='LAUREL WREATH'
            self.logoref='T-3844'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'HOLE SHANK BUTTON 100214985':
            self.logo='WREATH'
            self.logoref='D-866'
            self.finish_ref='TG-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100215284':
            self.logo='WORK-WEAR'
            self.logoref='T-5784'
            self.finish_ref='TS-411006'
        elif self.product_template_id.name == 'SNAP BUTTON 100215290':
            self.logo='WORK-WEAR'
            self.logoref='T-4998'
            self.finish_ref='TS-411006'
        elif self.product_template_id.name == 'D RING 100072579':
            self.logo='RALPH LAUREN'
            self.logoref='A-1925'
        elif self.product_template_id.name == 'D RING 100100335':
            self.logo='RALPH LAUREN'
            self.logoref='A-1925'
        elif self.product_template_id.name == 'SHANK BUTTON 100217764':
            self.logo='CLASSIC POLO RALPH LAUREN'
            self.logoref='T-3844'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100217661':
            self.logo='WAVY POLO'
            self.logoref='T-5252'
            self.finish_ref='TS-4117'
        elif self.product_template_id.name == 'SNAP BUTTON 100217813':
            self.logo='WORK-WEAR'
            self.logoref='T-5784'
            self.finish_ref='TS-411703'
        
                
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

    def _check_mrp (self):
        if self.order_id.sales_type == 'oa':
            mrp_ope = self.env['operation.details'].search([('company_id', '=', self.env.company.id),('oa_id', '=', self.order_id.id),('next_operation', '=', 'FG Packing'),('qty', '>', 0)])
            
            for li in self.ids:
                exist_ope = mrp_ope.filtered(lambda op: str(li) in op.sale_lines)
                if exist_ope:
                    # raise UserError((self.ids))
                    return True
                else:
                    return False
        else:
            return False
        
    def unlink(self):
        if self._check_line_unlink():
            raise UserError(_('You can not remove an order line once the sales order is confirmed.\nYou should rather set the quantity to 0.'))
        elif self._check_mrp():
            raise UserError(_('You can not remove an order line once the OA is in Production.\nYou should rather update the data'))
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

    @api.onchange('shade_name', 'shade_ref')
    def shade_change(self):
        for re in self:
            if re.shade_ref:
                if re.shade_name:
                    re.shade = re.shade_name + '\n' + re.shade_ref
                else:
                    re.shade = re.shade_ref
            elif re.shade_name:
                if re.shade_ref:
                    re.shade = re.shade_name + '\n' + re.shade_ref
                else:
                    re.shade = re.shade_name
                

        
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
            all_rm = self.env['product.product'].sudo().search([('default_code','ilike', 'R_'),('product_tmpl_id.company_id','=',self.env.company.id)])
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
        
                    con_tape = con_wire = con_slider = con_top = con_bottom = con_pinboc = rmc_val = 0       
                    if formula.tape_python_compute:
                        con_tape = safe_eval(formula.tape_python_compute, {'s': size, 'g': line.gap})
                        if wastage_tape:
                            if wastage_tape.wastage>0:
                                con_tape += (con_tape*wastage_tape.wastage)/100
                        line.tape_con = round(con_tape*line.product_uom_qty,4)
                        if con_tape > 0:
                            rm_pro = self.env['product.template'].sudo().search([('name','=', line.dyedtape)])
                            if rm_pro:
                                bom_pro = self.env['mrp.bom.line'].sudo().search([('bom_id.product_tmpl_id','=', rm_pro[0].id),('product_id.default_code','ilike','R_')])
                                if bom_pro:
                                    st_price = self.env['stock.production.lot'].sudo().search([('product_id','=', bom_pro[0].product_id.id)],order='id desc',limit=1)
                                    if st_price:
                                        price = st_price.unit_price
                                        rmc_val += (con_tape * line.product_uom_qty * price) + (con_tape * line.product_uom_qty * 0.50)
        
                    if formula.wair_python_compute:
                        con_wire = safe_eval(formula.wair_python_compute, {'s': size})
                        if wastage_wire:
                            if wastage_wire.wastage>0:
                                con_wire += (con_wire*wastage_wire.wastage)/100
                        line.wire_con = round(con_wire*line.product_uom_qty,4)
                        if con_wire > 0:
                            pro_id = None
                            if 'M#4' in line.product_id.product_tmpl_id.fg_categ_type.name:
                                pro_id = 23805
                            elif 'M#5' in line.product_id.product_tmpl_id.fg_categ_type.name:
                                pro_id = 27617
                            elif 'M#8' in line.product_id.product_tmpl_id.fg_categ_type.name:
                                pro_id = 24045
                            else:
                                pro_id = 23804
                            st_price = self.env['stock.production.lot'].sudo().search([('product_id','=', pro_id)],order='id desc',limit=1)
                            if st_price:
                                price = st_price.unit_price
                                rmc_val += (con_wire * line.product_uom_qty * price)
                                rmc_val += (line.tape_con + line.wire_con) * 0.80
                    
                    if formula.slider_python_compute:
                        con_slider = safe_eval(formula.slider_python_compute)
                        if wastage_slider:
                            if wastage_slider.wastage>0:
                                con_slider += (con_slider*wastage_slider.wastage)/100
                        line.slider_con = round(con_slider*line.product_uom_qty,4)
                        if con_slider > 0 and 'TZP' in line.slidercodesfg:
                            slider = None
                            if line.slidercodesfg:
                                findslider = line.slidercodesfg.find("TZP ")
                                if findslider > 0:
                                    slider = line.slidercodesfg.split("TZP ",1)[1]
                                else:
                                    slider = line.slidercodesfg.split("TZP-",1)[1]
                                rm_pro = all_rm.search([('product_tmpl_id.name','ilike', slider),('product_tmpl_id.name','ilike', 'TZP')],order='id desc',limit=1)
                                if rm_pro:
                                    st_price = self.env['stock.production.lot'].sudo().search([('product_id','=', rm_pro.id)],order='id desc',limit=1)
                                    if st_price:
                                        price = st_price.unit_price
                                        rmc_val += (con_slider * line.product_uom_qty * price)
                                        rmc_val += (((line.slider_con * 2.08) / 1000) * 1.50)
                    
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
                        if con_pinbox > 0:
                            pro_id = None
                            if line.product_id.product_tmpl_id.id in (43541,43550):
                                pro_id = 23923
                            elif line.product_id.product_tmpl_id.id in (43544,43553):
                                pro_id = 23922
                            elif line.product_id.product_tmpl_id.id in (43568,43562,43559,43571):
                                pro_id = 24047
                            elif line.product_id.product_tmpl_id.id in (43624,125283,43615):
                                pro_id = 24189
                            elif line.product_id.product_tmpl_id.id in (43627,125216,125284,43618):
                                pro_id = 24188
                            if pro_id:
                                st_price = self.env['stock.production.lot'].sudo().search([('product_id','=', pro_id)],order='id desc',limit=1)
                                if st_price:
                                    price = st_price.unit_price
                                    rmc_val += (con_pinbox * line.product_uom_qty * price)
                                
                    line.rmc = rmc_val
