# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import uuid
import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Attendee(models.Model):
    """ Calendar Attendee Information """
    _inherit = 'calendar.attendee'
    # _rec_name = 'common_name'
    # _description = 'Calendar Attendee Information'

    # partner_id = fields.Many2one('res.partner', 'Contact', required=False, readonly=True)

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            # if 'partner_id' in values:
            #     raise UserError((values.get('partner_id')))
            # by default, if no state is given for the attendee corresponding to the current user
            # that means he's the event organizer so we can set his state to "accepted"
            if values.get('partner_id') == False:
                # raise UserError((values.get('partner_id')))
                values['partner_id'] = 3
            # if not values.get("email") and values.get("common_name"):
            #     common_nameval = values.get("common_name").split(':')
            #     email = [x for x in common_nameval if '@' in x]
            #     values['email'] = email[0] if email else ''
            #     values['common_name'] = values.get("common_name")
        attendees = super().create(vals_list)
        # attendees._subscribe_partner()
        return attendees