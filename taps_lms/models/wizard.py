from odoo import models, fields, api


class Wizard(models.TransientModel):
    _name = 'lms.wizard'
    _description = "Wizard: Quick Registration of Attendees to Sessions"

    def _default_sessions(self):
        return self.env['lms.session'].browse(self._context.get('active_ids'))

    session_ids = fields.Many2many('lms.session',
                                   string="Sessions", required=True, default=_default_sessions)
    attendee_ids = fields.Many2many('hr.employee', string="Attendees")

    def subscribe(self):
        for session in self.session_ids:
            session.attendee_ids |= self.attendee_ids
        return {}