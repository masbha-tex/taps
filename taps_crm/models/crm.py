
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, api


class TapsCrm(models.Model):
    _inherit = 'crm.lead'
    _description = 'Taps CRM'

   

    
    def action_send_whatsapp(self):
        compose_form_id = self.env.ref('whatsapp_mail_messaging.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi"
        
        ctx.update({
            'default_message': message,
            'default_partner_id': self.partner_id.id,
            'default_mobile': self.partner_id.mobile if self.partner_id.mobile else self.partner_id.phone,
            'default_image_1920': self.partner_id.image_1920,
        })
        # raise UserError((ctx['default_mobile']))
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }
