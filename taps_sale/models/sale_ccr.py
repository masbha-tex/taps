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
    
    


        

    # @api.onchange('oa_number')
    # def dynamic_selection_onchange(self, id):
        

    
    
        

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
    sale_order_line_id = fields.Many2many('sale.order.line', string="Sale Order Line")
    fg_product = fields.Many2one('product.template',string="Product Type/Code", domain="[['categ_id.complete_name','ilike','ALL / FG']]" )
    finish = fields.Many2one('product.attribute.value', domain="[['attribute_id','=',4]]")
    # slider = fields.Char(string="Slider")
    sale_representative = fields.Many2one('sale.representative', related = 'oa_number.sale_representative', string='Sale Representative')
    team = fields.Many2one(related ='sale_representative.team', string='Team')
    team_leader = fields.Many2one(related ='sale_representative.leader', string='Team Leader')
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
    ca_lead = fields.Char(string='CA Lead', compute='_compute_ca_lead')
    pa_lead = fields.Char(string='PA Lead', compute='_compute_pa_lead')
    total_lead = fields.Char(string='Total Lead', compute='_compute_total_lead')
    cost = fields.Float(string='Cost', readonly=True)

    states = fields.Selection([
        ('draft', 'Draft'),
        ('inter', 'Intermediate'),
        ('just', 'Justified'),
        ('nonjust', 'Non justified'),
        ('ca', 'CA'),
        ('pa', 'PA'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=5, default='draft')

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket Number', readonly=True)

    last_approver = fields.Many2one(
        string="Last Approver",
        comodel_name="res.users",
        compute='_compute_last_approver'
        # default=lambda self: self.env.user.id
        
        
    )
    
    last_approve_date = fields.Date(string="Last Approve Date")

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
            if record.report_date and record.last_approve_date:
                d1=datetime.strptime(str(record.last_approve_date),'%Y-%m-%d')
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
                

    def _compute_last_approver(self):
        domain = ['&', '&', ('model', '=', 'sale.ccr'), ('res_id', 'in', self.ids), ('approved', '=', 'True')]
        
        # create dictionary of purchase.order res_id: last approver user_id
        groups = self.env['studio.approval.entry'].sudo().read_group(domain, ['ids:array_agg(id)'], ['res_id'])
        ccr_last_approver = {i['res_id']: max(i['ids']) for i in groups}
        # User = self.env['res.users']
        # docs = self.env['sale.ccr'].search(['id', 'in', 'draft'])
        Entry = self.env['studio.approval.entry']
        for rec in self:
            if rec.id in ccr_last_approver:
                rec.last_approver = Entry.browse(ccr_last_approver[rec.id]).user_id
                rec.last_approve_date = date.today()
            else:
                # raise UserError((Entry))
                rec.last_approver = False

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
        if self.rejected_quantity < 1 or not self.fg_product or not self.finish or not self.complaint or not self.invoice_reference:
            raise UserError(("You Cannot leave empty any of the following fields: \n -Rejected Quantity, \n -Product Type/Code, \n -Complain/Defeat, Invoice Ref. \n Kindly fill up all the fields and then assign to Quality"))
            
        else:
            
            # self.show_notification()
            
            post_vars = {
                       'subject': "CCR",
                       'body': "@" + self.env.user.partner_id.name,
                       'partner_ids': [self.env.user.partner_id.id],  # Where "4" adds the ID to the list of followers, and "19" is the partner ID
                    }
            
            res=self.env['mail.message'].create({
                'model': self._name,
                'res_id': self.id,
                'message_type': 'comment',
                'subtype_id': self.env.ref('mail.mt_comment').id,
                'subject': post_vars.get('subject'),
                'body': post_vars.get('body'),
                'partner_ids': post_vars.get('partner_ids'),
            })
            # raise UserError((res['partner_ids']))
            self.write({'states': 'inter'})
    
    def action_close(self):
        # self._compute_last_approver()
        self.write({'states': 'done'})
        return {}

    def action_smart_button(self):
        return {}

    def action_justify(self):
        if not self.ccr_type or not self.department_id or not self.analysis_activity:
            raise UserError(("You Cannot leave empty any of the the fields: \n -Ccr Type, \n -Resp. Department and \n -Probable Root Cause/Analysis"))
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
            'default_pa_closing_date': date.today(),
            
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
        if not self.ccr_type or not self.department_id or not self.analysis_activity:
            raise UserError(("You Cannot leave empty any of the the fields: \n -Ccr Type, \n -Resp. Department and \n -Probable Root Cause/Analysis"))

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