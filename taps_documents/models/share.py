# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, api, exceptions
from odoo.tools.translate import _
from odoo.tools import consteq

from odoo.osv import expression

import uuid


class DocumentShare(models.Model):
    _inherit = 'documents.share'

    name = fields.Char(string="Name")
    receiver_ids = fields.Many2many('res.partner','documents_share_email_rel','document_ids', 'partner_id', string="Email Notify")
