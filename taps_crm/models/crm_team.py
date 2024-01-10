from odoo import fields, models


class CrmTeamInherit(models.Model):
    _inherit = 'crm.team'


    core_leader = fields.Many2one('res.users' , string='Core Leader')
    region = fields.Many2one('team.region' , string='Region')
    