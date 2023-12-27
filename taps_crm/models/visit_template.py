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


class VisitPurpose(models.Model):
    _name = 'crm.visit.purpose'
    _description = 'Visit Purposes'
    _order = "id desc"

    name = fields.Char(string="Purpose/Objective")
    
class CustomerVisit(models.Model):

    _name = 'crm.visit'
    _description = 'Customer Visit Template'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    description = fields.Char(string="Description")
    partner_id = fields.Many2one('res.partner', string='Customer')
    buyer = fields.Many2one('res.partner', string='Buyer')
    concern = fields.Char(string="Concern")
    designation = fields.Char(string="Designation")
    mobile = fields.Char(string="Mobile")
    product = fields.Many2many('crm.tag', string="Product")
    visit_purpose = fields.Many2one('crm.visit.purpose',string="Visit Purpose")
    visit_outcome = fields.Text(string="Visit Outcome")
    action = fields.Text(string="Action")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True, default=lambda self: self.env.user)
    visit_date = fields.Date(string='Date', tracking=True, default=date.today())
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', index=True, tracking=True,
        compute='_compute_team_id', readonly=False, store=True)
    stages = fields.Selection([
        ('1_draft', 'Draft'),
        ('2_done', 'Done'),
        ('9_cancel', 'Cancel'),], 
        string='Status', copy=False, index=True, tracking=2, default='1_draft')
    color = fields.Integer('Color Index', default=0)



    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        
        self.check_access_rights('read')
        povalue = 0
        # raise UserError(('hi'))
        result = {
            'marketing': 0,#all_to_send
            'brahmaputra': 0,#all_waiting
            'meghna': 0,#all_late
            
            'shitalakhya': 0,
            'karnaphuli': 0,
            'padma': 0,
            'teesta': 0,
            'sangu': 0,#all_avg_order_value
            'jamuna': 0,#all_avg_days_to_purchase
            'halda': 0,#all_total_last_7_days
            'turag': 0,#all_sent_rfqs
            'total': 0,
            
        }

        # currency = self.env.company.currency_id
        # result['company'] = self.env.company.id
        current_datetime = date.today()


        first_date_of_current_month = current_datetime.replace(day=1)
        last_date_of_current_month = first_date_of_current_month + relativedelta(day=31)
        # raise UserError((last_date_of_current_month))
       
        visit = self.env['crm.visit'].search([('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        
        result['marketing'] = visit.search_count([('team_id.name', '=', 'MARKETING'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['brahmaputra'] = visit.search_count([('team_id.name', '=', 'BRAHMAPUTRA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['meghna'] = visit.search_count([('team_id.name', '=', 'MEGHNA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['shitalakhya'] = visit.search_count([('team_id.name', '=', 'SHITALAKHYA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['karnaphuli'] = visit.search_count([('team_id.name', '=', 'KARNAPHULI'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['padma'] = visit.search_count([('team_id.name', '=', 'PADMA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['teesta'] = visit.search_count([('team_id.name', '=', 'TEESTA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['sangu'] = visit.search_count([('team_id.name', '=', 'SANGU'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['jamuna'] = visit.search_count([('team_id.name', '=', 'JAMUNA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['halda'] = visit.search_count([('team_id.name', '=', 'HALDA'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['turag'] = visit.search_count([('team_id.name', '=', 'TURAG'),('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        result['total'] = visit.search_count([('visit_date', '>=', first_date_of_current_month),('visit_date', '<=', last_date_of_current_month)])
        # raise UserError((result['brahmaputra']))
        
        return result


    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.crm.visit', sequence_date=seq_date) or _('New')
        result = super(CustomerVisit, self).create(vals)
        return result


    @api.depends('user_id')
    def _compute_team_id(self):
        """ When changing the user, also set a team_id or restrict team id
        to the ones user_id is member of. """
        for lead in self:
            # setting user as void should not trigger a new team computation
            if not lead.user_id:
                continue
            user = lead.user_id
            if lead.team_id and user in lead.team_id.member_ids | lead.team_id.user_id:
                continue
            # team_domain = [('use_leads', '=', True)] if lead.type == 'lead' else [('use_opportunities', '=', True)]
            team = self.env['crm.team']._get_default_team_id(user_id=user.id, domain=None)
            lead.team_id = team.id


    def action_done(self):
        self.write({'stages': '2_done'})

    def action_cancel(self):
        self.write({'stages': '9_cancel'})
    def action_set_draft(self):
        self.write({'stages': '1_draft'})