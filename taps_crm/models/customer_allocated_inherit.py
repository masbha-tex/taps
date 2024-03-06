import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class CrmCustomerAllocated(models.Model):

    _inherit = 'customer.allocated'

    visit_count = fields.Integer( string='Visit count', compute='_compute_visit_for_individuals')
    visit_ids = fields.Many2many('crm.visit', string= "Visit", compute='_compute_visit_for_individuals')


    def view_visit(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Visits',
            'view_mode': 'tree',
            'res_model': 'crm.visit',
            'domain': [('user_id', '=', self.salesperson.id)],
            'context': "{'create': False}"
        }

    def _compute_visit_for_individuals(self):
        for record in self:
            visit = record.env['crm.visit'].sudo().search([('user_id', '=', self.salesperson.id)])
            record.visit_ids = visit
            record.visit_count = len(visit)

    