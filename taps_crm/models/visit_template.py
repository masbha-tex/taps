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
    product = fields.Many2one('crm.tag', string="Product")
    visit_purpose = fields.Many2one('crm.visit.purpose',string="Visit Purpose")
    visit_outcome = fields.Char(string="Visit Outcome")
    action = fields.Char(string="Action")
    user_id = fields.Many2one('res.users', string='Salesperson', index=True, tracking=True, default=lambda self: self.env.user)
    visit_date = fields.Date(string='Date', tracking=True, default=date.today())
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)
    team_id = fields.Many2one(
        'crm.team', string='Sales Team', index=True, tracking=True,
        compute='_compute_team_id', readonly=False, store=True)
    stages = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),], 
        string='Status', copy=False, index=True, tracking=2, default='draft')


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
        self.write({'stages': 'done'})

    def action_cancel(self):
        self.write({'stages': 'cancel'})
    def action_set_draft(self):
        self.write({'stages': 'draft'})