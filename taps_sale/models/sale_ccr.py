from num2words import num2words
import base64
from datetime import datetime, timedelta, date
from dateutil.relativedelta import relativedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
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
from urllib.parse import quote



class ResPartner(models.Model):
    _inherit = 'res.partner'

    ccr_count = fields.Integer(compute='_compute_ccr_count', string='CCR Count')

    def action_view_ccr(self):
        return {}
    def _compute_ccr_count(self):
        self.ccr_count = 0
        # retrieve all children partners and prefetch 'parent_id' on them
        # all_partners = self.with_context(active_test=False).search([('id', 'child_of', self.ids)])
        # all_partners.read(['parent_id'])

        # sale_order_groups = self.env['sale.order'].read_group(
        #     domain=[('partner_id', 'in', all_partners.ids)],
        #     fields=['partner_id'], groupby=['partner_id']
        # )
        # partners = self.browse()
        # for group in sale_order_groups:
        #     partner = self.browse(group['partner_id'][0])
        #     while partner:
        #         if partner in self:
        #             partner.sale_order_count += group['partner_id_count']
        #             partners |= partner
        #         partner = partner.parent_id
        # (self - partners).sale_order_count = 0


class CcrType(models.Model):
    _name = 'sale.ccr.type'
    _description = 'CCR COMPLAINT Type'
    _order = 'id desc'

    name = fields.Char(string="CCR Type")
    
class SaleCcr(models.Model):
    _name = 'sale.ccr'
    _description = 'CCR COMPLAINT'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'id desc'
    _check_company_auto = True
    
    


        

    # @api.model
    # def _default_fg_product(self):
    #     raise UserError((self))
    #     if self.oa_number:
    #         sale_order_lines = self.oa_number.order_line.filtered(lambda line: line.product_id)
    #         product_id = sale_order_lines and sale_order_lines[0].product_id.id or False
    #         return product_id
    #     else:
    #         return False

    
    
        

    name = fields.Char(string='CCR Reference', required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    oa_number = fields.Many2one('sale.order', string='OA Number', readonly=True)
    customer = fields.Many2one('res.partner',related = 'oa_number.partner_id', string='Customer')
    buyer = fields.Many2one('res.partner',related = 'oa_number.buyer_name', string='Buyer')
    pi_number = fields.Many2one('sale.order', related = 'oa_number.order_ref',string='PI Number')
    order_quantity = fields.Float(related = 'oa_number.order_ref.total_product_qty',string='Order Quantity')
    rejected_quantity = fields.Float(string='Rejected Quantity')
    ccr_type= fields.Many2one('sale.ccr.type',string='CCR Type')
    complaint = fields.Text(string='Complaint/Defeat')
    department_id = fields.Many2one('hr.department', string='Resp. Department')
    replacement_return_qty = fields.Float(string='Replacement Return Quantity')
    replacement_quantity = fields.Float(string='Replacement Quantity', readonly=True)
    replacement_value = fields.Float(string='Replacement Value')
    analysis_activity = fields.Text(string='Probable Root Cause/Analysis')
    corrective_action = fields.Text(string='Corrective Action', readonly=True)
    preventive_action = fields.Text(string='Preventive Action',readonly=True)
    non_justify_action = fields.Text(string='Action to be taken',readonly=True)
    ca_closing_date = fields.Date(string='CA Closing Date',readonly=True)
    pa_closing_date = fields.Date(string='PA Closing Date',readonly=True)
    closing_date = fields.Date(string='Closing Date')
    fg_product = fields.Many2one('product.template',string="Product Type/Code", domain="[['categ_id.complete_name','ilike','ALL / FG']]")
    # fg_product = fields.Many2one(
    #     'product.template',
    #     string="Product Type/Code",
        
    #      # You can set a default value if needed
    # )
    finish = fields.Many2one('product.attribute.value', domain="[['attribute_id','=',4]]")
    # slider = fields.Char(string="Slider")
    sale_representative = fields.Many2one('res.users', related = 'oa_number.user_id', string='Salesperson')
    team = fields.Many2one(related ='oa_number.team_id', string='Team')
    # team_leader = fields.Many2one(related ='sale_representative.leader', string='Team Leader')
    company_id = fields.Many2one(related='oa_number.company_id', string='Company', store=True, readonly=True, index=True)
    invoice_reference = fields.Char(string='Invoice Ref.')
    report_date = fields.Date(string='Report Date', default= date.today(), readonly=True)
    reason = fields.Text(string="Reason for Not Justified", readonly=True)
    # justification_level = fields.Selection(
    #     [('justified','Justified'),
    #      ('notjustified','Not Justified')],
    #     'State', store=True)
    justification = fields.Char('Justification Status', readonly=True)
    after_sales = fields.Char('After Sales Service', readonly=True)
    replacement_item = fields.Char('Replacement Item', readonly=True)
    ca_lead = fields.Char(string='CA Lead', compute='_compute_ca_lead')
    pa_lead = fields.Char(string='PA Lead', compute='_compute_pa_lead')
    total_lead = fields.Char(string='Total Lead', compute='_compute_total_lead')
    cost = fields.Float(string='Cost', readonly=True)
    ca_step_1 = fields.Char(string='CA Step 1', readonly=True)
    ca_step_2 = fields.Char(string='CA Step 2', readonly=True)
    ca_step_3 = fields.Char(string='CA Step 3', readonly=True)
    pa_step_1 = fields.Char(string='PA Step 1', readonly=True)
    pa_step_2 = fields.Char(string='PA Step 2', readonly=True)
    pa_step_3 = fields.Char(string='PA Step 3', readonly=True)

    states = fields.Selection([
        ('draft', 'Draft'),
        ('inter', 'Intermediate'),
        ('just', 'Justified'),
        ('nonjust', 'Non justified'),
        ('ca', 'CA'),
        ('pa', 'PA'),
        ('man', 'Manufacturing'),
        ('toclose', 'To Close'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=5, default='draft')

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket Number', readonly=True)
    raised_by = fields.Many2one('res.users', related ='ticket_id.create_uid', string="Raised By" ,readonly=True)

    last_approver = fields.Many2one(
        string="Last Approver",
        comodel_name="res.users",
        # default=lambda self: self.env.user.id
        
        
    )
    
    # last_approve_date = fields.Date(string="Last Approve Date")

    # def _default_domain(self):
    #     order_products= self.oa_number.id
    #     # raise UserError((order_products))
    #     sale_order_line = self.env['sale.order.line'].search([('order_id', '=', order_products)])
    #     id = sale_order_line.mapped('product_template_id')
    #     # Your logic to calculate the domain goes here
    #     return "[['id', 'in', id]]"

    

        
    @api.model
    def retrieve_dashboard_ccr(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        total_qty=0
        total_value=0.0
        self.check_access_rights('read')
        povalue = 0
        # raise UserError(('hi'))
        result = {
            'quality': 0,#all_to_send
            'ca': 0,#all_waiting
            'pa': 0,#all_late
            
            'justified': 0,
            'notjustified': 0,
            'closed': 0,
            'production': 0,
            'sales': 0,#all_avg_order_value
            'ceo': 0,#all_avg_days_to_purchase
            'total_qty': 0,#all_total_last_7_days
            'total_value': 0,#all_sent_rfqs
            
        }
        ccr = self.env['sale.ccr'].search([])
        for rec in self.env['sale.ccr'].search([('states','=','done')]):
            if rec.replacement_quantity and rec.cost:
                total_qty += rec.replacement_quantity
                total_value += rec.cost
            
        
        result['quality'] = ccr.search_count([('states', '=', 'inter')])
        result['ca'] = ccr.search_count([('states', '=', 'just')])
        result['pa'] = ccr.search_count([('states', '=', 'ca')])
        result['justified'] = ccr.search_count([('states', '=', 'done'),('justification', '=', 'Justified')])
        result['notjustified'] = ccr.search_count([('states', '=', 'done'),('justification', '=', 'Not Justified')])
        result['closed'] = ccr.search_count([('states', '=', 'done')])
        result['production'] = ccr.search_count([['states', 'in', ['pa','nonjust']]])
        result['sales'] = ccr.search_count([('last_approver', '=', 20)])
        result['ceo'] = ccr.search_count([('last_approver', '=', 88)])
        
        result['total_qty'] = total_qty
        result['total_value'] = total_value
        # raise UserError((result['notjustified']))
        
        return result

    def show_notification(self):
        
        notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Your Custom Title'),
                'message': 'Your Custom Message',
                'type':'success',  #types: success,warning,danger,info
                'sticky': True,  #True/False will display for few seconds if false
            },
        }
        # raise UserError((notification))
        return notification

    

    def _compute_ca_lead(self):
        for record in self:
            if record.report_date and record.ca_closing_date:
                d1=datetime.strptime(str(record.ca_closing_date),'%Y-%m-%d')
                d2=datetime.strptime(str(record.report_date),'%Y-%m-%d')
                record.ca_lead = str((d1-d2).days) + " days"
            else: 
                record.ca_lead = '0 days'

    def _compute_pa_lead(self):
        for record in self:
            if record.ca_closing_date and record.pa_closing_date:
                d1=datetime.strptime(str(record.pa_closing_date),'%Y-%m-%d')
                d2=datetime.strptime(str(record.ca_closing_date),'%Y-%m-%d')
                record.pa_lead = str((d1-d2).days) + " days"
            else: 
                record.pa_lead = '0 days'
                
    def _compute_total_lead(self):
        for record in self:
            if record.report_date and record.closing_date:
                d1=datetime.strptime(str(record.closing_date),'%Y-%m-%d')
                d2=datetime.strptime(str(record.report_date),'%Y-%m-%d')
                record.total_lead = str((d1-d2).days) + " days"
            else: 
                record.total_lead = '0 days'
        # for record in self:
        #     if record.justification == 'Justified':
        #         if record.pa_closing_date and record.last_approve_date:
        #             d1=datetime.strptime(str(record.last_approve_date),'%Y-%m-%d')
        #             d2=datetime.strptime(str(record.pa_closing_date),'%Y-%m-%d')
        #             record.total_lead = str((d1-d2).days) + " days"
        #         else:
        #             record.total_lead = '0 days'
        #     elif record.justification == 'Not Justified':
        #         if record.report_date and record.last_approve_date:
        #             d1=datetime.strptime(str(record.last_approve_date),'%Y-%m-%d')
        #             d2=datetime.strptime(str(record.report_date),'%Y-%m-%d')
        #             record.total_lead = str((d1-d2).days) + " days"
        #         else:
        #             record.total_lead = '0 days'
        #     else:
        #         record.total_lead = '0 days'
                

    # def _compute_last_approver(self):
    #     domain = ['&', '&', ('model', '=', 'sale.ccr'), ('res_id', 'in', self.ids), ('approved', '=', 'True')]
        
    #     # create dictionary of purchase.order res_id: last approver user_id
    #     groups = self.env['studio.approval.entry'].sudo().read_group(domain, ['ids:array_agg(id)'], ['res_id'])
    #     ccr_last_approver = {i['res_id']: max(i['ids']) for i in groups}
    #     # User = self.env['res.users']
    #     # docs = self.env['sale.ccr'].search(['id', 'in', 'draft'])
    #     Entry = self.env['studio.approval.entry']
    #     for rec in self:
    #         if rec.id in ccr_last_approver:
    #             rec.last_approver = Entry.browse(ccr_last_approver[rec.id]).user_id
    #             rec.last_approve_date = date.today()
    #         else:
    #             # raise UserError((Entry))
    #             rec.last_approver = False

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.ccr', sequence_date=seq_date) or _('New')
        
        result = super(SaleCcr, self).create(vals)
        return result
    
    def action_cancel(self):
        self.write({'states': 'cancel'})
        return {}
    def action_draft(self):
        self.write({'states': 'draft'})
        return {}
        
    def action_assign_quality(self):
        if not self.fg_product or not self.finish or not self.complaint or not self.invoice_reference:
            raise UserError(("You Cannot leave empty any of the following fields:\n -Product Type/Code, \n -Complain/Defeat, Invoice Ref. \n Kindly fill up all the fields and then assign to Quality"))
            
        else:
            self.write({'states': 'inter'})
            self.ticket_id.stage_id = 2
            email_cc_list=['alamgir@texzipperbd.com',
                           'nitish.bassi@texzipperbd.com',
                           self.ticket_id.create_uid.partner_id.email,
                          ]
            email_to_list=[]
            email_from_list=['odoo@texzipperbd.com']
            if self.company_id.id == 1:
                email_cc_list.append('ranjeet.singh@texzipperbd.com')
                email_to_list.append('qa@bd.texfasteners.com')
                # email_from_list.append('csd.zipper@texzipperbd.com')
            if self.company_id.id == 3:
                email_cc_list.append('kumar.abhishek@texzipperbd.com')
                email_to_list.append('quality2.metaltrims@texzipperbd.com')
                email_to_list.append('quality4.metaltrims@texzipperbd.com')
                
                # email_from_list.append('nasir.csd@texzipperbd.com')

            email_cc = ','.join(email_cc_list)
            email_to = ','.join(email_to_list)
            email_from = ','.join(email_from_list)
            template_id = self.env.ref('taps_sale.ccr_assign_quality_email_template')
            
            if template_id:
                template_id.write({
                    'email_to': email_to,
                    'email_from': email_from,
                    'email_cc' : email_cc,
                })
                
                template_id.send_mail(self.id, force_send=False)



    def action_manufacturing(self):
        # raise UserError((self._uid))
        # self._uid == 20
        if self._uid == 20:
            self.write({'states': 'man', 'last_approver': self._uid})
            # email_cc_list=['alamgir@texzipperbd.com','nitish.bassi@texzipperbd.com']
            # email_to_list=[]
            # email_from_list=[]
            # if self.company_id.id == 1:
            #     email_cc_list.append('ranjeet.singh@texzipperbd.com')
            #     email_to_list.append('qa@bd.texfasteners.com')
            #     email_from_list.append('csd.zipper@texzipperbd.com')
            # if self.company_id.id == 3:
            #     email_cc_list.append('kumar.abhishek@texzipperbd.com')
            #     email_to_list.append('quality2.metaltrims@texzipperbd.com')
            #     email_from_list.append('nasir.csd@texzipperbd.com')

            # email_cc = ','.join(email_cc_list)
            # email_to = ','.join(email_to_list)
            # email_from = ','.join(email_from_list)
            template_id = self.env.ref('taps_sale.ccr_assign_sales_confirmation_template')
            if template_id:
                template_id.write({
                    'email_to': 'alamgir@texzipperbd.com',
                    'email_from': 'odoo@texzipperbd.com',
                    'email_cc' : 'asraful.haque@texzipperbd.com',
                })
                
                template_id.send_mail(self.id, force_send=False)
            
        else:
            notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Warning'),
                'message': 'Only Mr. Nitish Bassi Can Approve This',
                'type':'warning',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
                    },
                        }
            return notification
            
    def action_sales(self):
        # self._uid == 88:
        if self._uid == 88:
            # Update the record's state and last_approver
            self.write({'states': 'toclose', 'last_approver': self._uid})
            # email_cc_list=['alamgir@texzipperbd.com','nitish.bassi@texzipperbd.com']
            # email_to_list=[]
            # email_from_list=[]
            # if self.company_id.id == 1:
            #     email_cc_list.append('ranjeet.singh@texzipperbd.com')
            #     email_to_list.append('qa@bd.texfasteners.com')
            #     email_from_list.append('csd.zipper@texzipperbd.com')
            # if self.company_id.id == 3:
            #     email_cc_list.append('kumar.abhishek@texzipperbd.com')
            #     email_to_list.append('quality2.metaltrims@texzipperbd.com')
            #     email_from_list.append('nasir.csd@texzipperbd.com')

            # email_cc = ','.join(email_cc_list)
            # email_to = ','.join(email_to_list)
            # email_from = ','.join(email_from_list)
            template_id = self.env.ref('taps_sale.ccr_assign_ceo_confirmation_template')
            if template_id:
                template_id.write({
                    'email_to': 'deepak.shah@bd.texfasteners.com',
                    'email_from': 'odoo@texzipperbd.com',
                    'email_cc' : 'asraful.haque@texzipperbd.com',
                })
                
                template_id.send_mail(self.id, force_send=False)
            
            
        else:
            notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Warning'),
                'message': 'Only Alamgir Shohag Can Approve This',
                'type':'warning',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
                    },
                        }
            return notification
    
    def action_close(self):
        # self._compute_last_approver()
        # self._uid == 17:
        if self._uid == 17:
            self.write({'states': 'done', 'closing_date':date.today()})
            self.ticket_id.stage_id= 3

        else:
            notification = {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': ('Warning'),
                'message': 'Only Deepakkumar Mukundkumar Shah Can Approve This',
                'type':'warning',  #types: success,warning,danger,info
                'sticky': False,  #True/False will display for few seconds if false
                    },
                        }
            return notification
        

    def action_smart_button(self):
        return {}

    def action_justify(self):
        if not self.ccr_type or not self.analysis_activity:
            raise UserError(("You Cannot leave empty any of the the fields: \n -Ccr Type, \n -Probable Root Cause/Analysis"))
        else:
            self.write({'states': 'just'})
            self.write({'justification': 'Justified'})
        return {}
        
    def action_corrective(self):
        compose_form_id = self.env.ref('taps_sale.sale_ccr_wizard_form_ca').id
        ctx = dict(self.env.context)
        
        # raise UserError((self.id))
        ctx.update({
            'default_ca_closing_date': date.today(),
            'default_ccr_no' : self.name,
            'default_oa_number' : self.oa_number.id,
            'default_pi_number' : self.oa_number.order_ref.id,
            'default_invoice_reference' : self.invoice_reference,
            'default_ccr_raised_by' : self.ticket_id.create_uid.id,
            'default_customer' : self.customer.id,
            'default_buyer' : self.buyer.id,
            'default_ccr_type' : self.ccr_type.id,
            'default_analysis_activity' : self.analysis_activity,
            
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.ccr.wizard.ca',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def action_preventive(self):
        compose_form_id = self.env.ref('taps_sale.sale_ccr_wizard_form_pa').id
        ctx = dict(self.env.context)
        
        # raise UserError((self.id))
        ctx.update({
            
            'default_ccr_no' : self.name,
            'default_oa_number' : self.oa_number.id,
            'default_pi_number' : self.oa_number.order_ref.id,
            'default_invoice_reference' : self.invoice_reference,
            'default_ccr_raised_by' : self.ticket_id.create_uid.id,
            'default_customer' : self.customer.id,
            'default_buyer' : self.buyer.id,
            'default_ccr_type' : self.ccr_type.id,
            'default_analysis_activity' : self.analysis_activity,
            'default_pa_closing_date': date.today(),
            'default_ca_step_1': self.ca_step_1,
            'default_ca_step_2': self.ca_step_2,
            'default_ca_step_3': self.ca_step_3,
            'default_after_sales': self.after_sales,
            'default_replacement_item': self.replacement_item,
            'default_replacement_quantity': self.replacement_quantity,
            'default_cost': self.cost,
            'default_ca_closing_date': self.ca_closing_date,
            
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.ccr.wizard.pa',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    
    def action_notjustify(self):
        if not self.ccr_type or not self.analysis_activity:
            raise UserError(("You Cannot leave empty any of the the fields: \n -Ccr Type,\n -Probable Root Cause/Analysis"))

        else:
            compose_form_id = self.env.ref('taps_sale.sale_ccr_wizard_form_notjustify').id
            
        
        # raise UserError((self.id))
        
            return {
                'type': 'ir.actions.act_window',
                'view_mode': 'form',
                'name' : 'Not Justify Form',
                'res_model': 'sale.ccr.wizard.notjustify',
                'views': [(compose_form_id, 'form')],
                'view_id': compose_form_id,
                'target': 'new',
            }