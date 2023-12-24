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
    oa_number = fields.Many2one('sale.order', string='OA Number')
    customer = fields.Many2one('res.partner',related = 'oa_number.partner_id', string='Customer')
    buyer = fields.Many2one('res.partner',related = 'oa_number.buyer_name', string='Buyer')
    pi_number = fields.Many2one('sale.order', related = 'oa_number.order_ref',string='PI Number')
    order_quantity = fields.Float(related = 'oa_number.order_ref.total_product_qty',string='Order Quantity')
    rejected_quantity = fields.Float(string='Rejected Quantity')
    ccr_type= fields.Many2one('sale.ccr.type',string='CCR Type')
    complaint = fields.Text(string='Complaint/Defeat')
    department_id = fields.Many2one('hr.department', string='Resp. Department')
    replacement_return_qty = fields.Float(string='Replacement Return Quantity')
    replacement_quantity = fields.Float(string='Replacement Quantity')
    replacement_value = fields.Float(string='Replacement Value')
    analysis_activity = fields.Text(string='Analysis Activity')
    corrective_action = fields.Text(string='Corrective Action')
    preventive_action = fields.Text(string='Preventive Action')
    cap_closing_date = fields.Date(string='Cap Closing Date')
    sale_order_line_id = fields.Many2many('sale.order.line', string="Sale Order Line")
    fg_product = fields.Many2one('product.template',string="Fg Products", domain="[['categ_id.complete_name','ilike','ALL / FG']]")
    finish = fields.Many2one('product.attribute.value', domain="[['attribute_id','=',4]]")
    # slider = fields.Char(string="Slider")
    sale_representative = fields.Many2one('sale.representative', related = 'oa_number.sale_representative', string='Sale Representative')
    team = fields.Many2one(related ='sale_representative.team', string='Team')
    team_leader = fields.Many2one(related ='sale_representative.leader', string='Team Leader')
    company_id = fields.Many2one(related='oa_number.company_id', string='Company', store=True, readonly=True, index=True)
    invoice_reference = fields.Char(string='Invoice Ref.')
    report_date = fields.Date(string='Report Date', default= date.today())
    reason = fields.Char(string="Reason for Not Justified")
    # justification_level = fields.Selection(
    #     [('justified','Justified'),
    #      ('notjustified','Not Justified')],
    #     'State', store=True)
    justification = fields.Char('Justification Status', readonly=True)

    states = fields.Selection([
        ('draft', 'Draft'),
        ('just', 'Justified'),
        ('nonjust', 'Non justified'),
        ('done', 'Closed'),
        ('cancel', 'Cancelled'),
        ], string='Status', readonly=True, copy=False, index=True, tracking=5, default='draft')

    ticket_id = fields.Many2one('helpdesk.ticket', string='Ticket Number')

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
    def action_close(self):
        self.write({'states': 'done'})
        return {}

    def action_smart_button(self):
        return {}

    def action_justify(self):
        self.write({'states': 'just'})
        self.write({'justification': 'Justified'})
        return {}
    def action_take(self):
        
        compose_form_id = self.env.ref('taps_sale.sale_ccr_wizard_form').id
        ctx = dict(self.env.context)
        
        # raise UserError((self.id))
        ctx.update({
            'default_cap_closing_date': date.today(),
            
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.ccr.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
    def action_notjustify(self):
        
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