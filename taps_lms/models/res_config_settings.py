from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    _description = 'Res Config Settings'

    session_allowed_seats = fields.Integer('Default allowed seats')
    session_duration = fields.Float('Default duration')
    group_stock_multi_lms = fields.Boolean('Multi-Warehouses', default=True, implied_group='taps_lms.group_stock_multi_lms')

    @api.model
    def set_values(self):
        ICP = self.env['ir.config_parameter'].sudo()
        ICP.set_param('taps_lms.session_allowed_seats', self.session_allowed_seats)
        ICP.set_param('taps_lms.session_duration', self.session_duration)
        super(ResConfigSettings, self).set_values()

    @api.model
    def get_values(self):
        ICP = self.env['ir.config_parameter'].sudo()
        res = super(ResConfigSettings, self).get_values()
        res['session_allowed_seats'] = int(ICP.get_param('taps_lms.session_allowed_seats'))
        res['session_duration'] = float(ICP.get_param('taps_lms.session_duration'))
        return res