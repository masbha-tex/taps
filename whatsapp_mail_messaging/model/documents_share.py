from itertools import groupby

from odoo import models, _
from odoo.exceptions import UserError


class DocumentShare(models.Model):
    _inherit = 'documents.share'

    def action_send_whatsapp(self):
        compose_form_id = self.env.ref('whatsapp_mail_messaging.whatsapp_message_wizard_form').id
        ctx = dict(self.env.context)
        message = "Hi, Here is the link: " + self.full_url
        ctx.update({
            'default_message': message,
            'default_partner_id': self.receiver_ids.id,
            'default_mobile': self.receiver_ids.mobile,
            # 'default_image_1920': self.receiver_ids.image_1920,
        })
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'whatsapp.message.wizard',
            'views': [(compose_form_id, 'form')],
            'view_id': compose_form_id,
            'target': 'new',
            'context': ctx,
        }

    def check_customers(self, partner_ids):
        partners = groupby(partner_ids)
        return next(partners, True) and not next(partners, False)

    # def action_whatsapp_multi(self):
    #     sale_order_ids = self.env['documents.share'].browse(self.env.context.get('active_ids'))
    #     partner_ids = []
    #     for sale in sale_order_ids:
    #         partner_ids.append(sale.partner_id.id)
    #     partner_check = self.check_customers(partner_ids)
    #     if partner_check:
    #         sale_numbers = sale_order_ids.mapped('name')
    #         sale_numbers = "\n".join(sale_numbers)
    #         compose_form_id = self.env.ref('whatsapp_mail_messaging.whatsapp_message_wizard_form').id
    #         ctx = dict(self.env.context)
    #         message = "Hi" + " " + self.partner_id.name + ',' + '\n' + "Your Orders are" + '\n' + sale_numbers + \
    #                   ' ' + '\n' + "is ready for review.Do not hesitate to contact us if you have any questions."
    #         ctx.update({
    #             'default_message': message,
    #             'default_partner_id': sale_order_ids[0].partner_id.id,
    #             'default_mobile': sale_order_ids[0].partner_id.mobile,
    #             'default_image_1920': sale_order_ids[0].partner_id.image_1920,
    #         })
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'view_mode': 'form',
    #             'res_model': 'whatsapp.message.wizard',
    #             'views': [(compose_form_id, 'form')],
    #             'view_id': compose_form_id,
    #             'target': 'new',
    #             'context': ctx,
    #         }
    #     else:
    #         raise UserError(_(
    #             'It seems that you have selected orders of more than one customer.'
    #             'Try select orders of an unique customer'))
