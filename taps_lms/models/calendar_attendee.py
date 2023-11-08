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
