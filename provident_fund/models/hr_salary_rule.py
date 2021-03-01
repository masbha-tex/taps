# -*- coding: utf-8 -*-

from odoo import fields, models

class HrSalaryRule(models.Model):
    _inherit = 'hr.salary.rule'

    is_providient_found = fields.Boolean("Providient Found")
