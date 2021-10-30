# -*- coding:utf-8 -*-

from odoo import fields, models


class WorkEntry(models.Model):
    _inherit = 'hr.work.entry'
    _description = 'Work entry'

    inFlag = fields.Char("In-Flag", readonly=True)
    outFlag = fields.Char("Out-Flag", readonly=True)
    otHours = fields.Float(string = "OT Hours")
    #overtime_id = fields.Many2one('hr.overtime')