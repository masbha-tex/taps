import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class CrmTeamTransfer(models.Model):
    _name = "crm.team.transfer"
    _inherit = ['mail.thread']
    _description = "Transfer To a new Sales Team"
    _order = "sequence"
    _check_company_auto = True


    sale_user_id = fields.Many2one('res.users', string='Sales Person', check_company=True)
    current_team = fields.Many2one('crm.team', string='Current Team', related='sale_user_id.sale_team_id', readonly=True)
    # current_team_leader = fields.Many2one('crm.team', string='Current Team Leader')
    new_team = fields.Many2one('crm.team', string='New Team')
    active_date = fields.Date(string='Activation Date')