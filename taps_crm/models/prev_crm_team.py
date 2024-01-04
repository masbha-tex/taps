# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class PrevCrmTeam(models.Model):
    _name = "prev.crm.team"
    _inherit = ['mail.thread']
    _description = "Previous Sales Team"
    _order = "sequence"
    _check_company_auto = True

    
    prev_team_id = fields.Many2one('crm.team',string='Previous Sales Team', required=True, translate=True)
    sequence = fields.Integer('Sequence', default=10)
    active = fields.Boolean(default=True, help="If the active field is set to false, it will allow you to hide the Sales Team without removing it.")
    company_id = fields.Many2one(
        'res.company', string='Company', index=True,
        default=lambda self: self.env.company)
    currency_id = fields.Many2one(
        "res.currency", string="Currency",
        related='company_id.currency_id', readonly=True)
    sale_user_id = fields.Many2one('res.users', string='Sales Person', check_company=True)
    user_id = fields.Many2one('res.users', string='Previous Team Leader', check_company=True)
    deactive_date = fields.Date(string="Deactivation Date")
    
    

    