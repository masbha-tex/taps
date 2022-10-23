# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"
    _description = "Employee Appraisal"


    ytd_weightage_acvd = fields.Float(string='YTD Weightage ACVD', compute='_compute_ytd_weightage_acvd')

    def _compute_ytd_weightage_acvd(self):
        for appraisal in self:
            app_goal = self.env['hr.appraisal.goal'].search([('employee_id', '=', appraisal.employee_id.id)])
            ytd = sum(app_goal.mapped('y_ytd'))
            appraisal.ytd_weightage_acvd = ytd
