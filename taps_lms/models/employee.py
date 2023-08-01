from odoo import models, fields, api


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    instructor = fields.Boolean("Instructor", default=False)
    session_ids = fields.Many2many('lms.session', string="Attended Sessions", readonly=True)
