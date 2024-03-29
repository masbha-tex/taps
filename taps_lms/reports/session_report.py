from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SessionReport(models.AbstractModel):
    _name = 'report.taps_lms.report_session_view'
    _description = 'Report Session View'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not self.env.user.has_group('taps_lms.group_manager_lms'):
            raise UserError('You do not have access to print this report!')
        sessions = self.env['lms.session'].browse(docids)
        for session in sessions:
            if len(session.attendee_ids) == 0:
                raise UserError(f"{session.display_name} have no attendees!")
        return {
            'doc_ids': docids,
            'doc_model': 'lms.session',
            'docs': self.env['lms.session'].browse(docids),
        }