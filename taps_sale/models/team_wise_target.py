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

class TeamWiseTarget(models.Model):
    _name = 'sale.target'
    _description = 'Team Wise Target'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']


    name = fields.Char(string="Name")
    user_id = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)
    date_from = fields.Date('Start Date', required=True, states={'done': [('readonly', True)]})
    date_to = fields.Date('End Date', required=True, states={'done': [('readonly', True)]})
    quarter = fields.Selection([
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4')
        ], 'Quarter', default='q1', index=True, required=True, copy=False, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
        ('validate', 'Validated'),
        ('done', 'Done')
        ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, tracking=True)
    target_line = fields.One2many('sale.target.lines', 'target_id', 'Target Lines',
        states={'done': [('readonly', True)]}, copy=True)
    company_id = fields.Many2one('res.company', 'Company', required=True,
        default=lambda self: self.env.company)


    def action_target_confirm(self):
        self.write({'state': 'confirm'})

    def action_target_draft(self):
        self.write({'state': 'draft'})

    def action_target_validate(self):
        self.write({'state': 'validate'})

    def action_target_cancel(self):
        self.write({'state': 'cancel'})

    def action_target_done(self):
        self.write({'state': 'done'})

    # def _compute_name(self):
    #     dateFrom = self.date_from.year
    #     dateTo = self.date_to.year
    #     quarter = self.quarter
    #     self.name = str(dateFrom)+"-"+str(dateTo)+"-"+str(quarter)
        


class TargetLines(models.Model):
    _name = "sale.target.lines"
    _description = "Target Line"

    name = fields.Char(compute='_compute_line_name')
    target_id = fields.Many2one('sale.target', 'Target', ondelete='cascade', index=True, required=True)
    # analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')
    # analytic_group_id = fields.Many2one('account.analytic.group', 'Analytic Group', related='analytic_account_id.group_id', readonly=True)
    team_id = fields.Many2one('sale.team', 'Team', required=True)
    date_from = fields.Date('Start Date', required=True)
    date_to = fields.Date('End Date', required=True)
    quarter = fields.Selection([
        ('q1', 'Q1'),
        ('q2', 'Q2'),
        ('q3', 'Q3'),
        ('q4', 'Q4')
        ], 'Quarter', required=True, copy=False,)
    paid_date = fields.Date('Paid Date')
    currency_id = fields.Many2one('res.currency', readonly=False)
    target_amount = fields.Monetary(
        'Target Amount', required=True,
        help="Amount you plan to earn")
    earned_amount = fields.Monetary(
        string='Earned Amount', help="Amount really earned")
    
    percentage = fields.Float(
        string='Achievement',
        help="Comparison between practical and theoretical amount. This measure tells you if you are below or over budget.")
    
    is_above_target = fields.Boolean()
    target_state = fields.Selection(related='target_id.state', string='Target State', store=True, readonly=True)




    # def _compute_percentage(self):
    #     for line in self:
    #         if line.theoritical_amount != 0.00:
    #             line.percentage = float((line.practical_amount or 0.0) / line.theoritical_amount)
    #         else:
    #             line.percentage = 0.00

    
    