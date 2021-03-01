# -*- coding:utf-8 -*-

from odoo import fields, models


class WorkEntry(models.Model):
    _inherit = 'hr.work.entry'
    _description = 'Work entry'

    overtime_id = fields.Many2one('hr.overtime')
