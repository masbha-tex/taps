# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, api, exceptions
from odoo.tools.translate import _
from odoo.tools import consteq

from odoo.osv import expression

import uuid


class DocumentShare(models.Model):
    _inherit = 'documents.share'

    receiver_ids = fields.Many2many('res.partner','documents_share_email_rel','document_ids', 'partner_id', string="Email Notify")

    sent_template = fields.Html('Sent Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Here you have been sent a file. Please click below button</span>
                    <br>
                    <br>
                    
                    <br>
                    		
                    			% if ctx.get('full_url'):
                    			Here is the link of :
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['full_url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View File
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )

    # def action_closed(self):
    #     # raise UserError(('goodbye'))
    #     # if self.state == 'Submit':
    #     #     self.issue_date = fields.Date.today()
    #     #     self.state = 'Approved'
    #     for mail in self:
    #         document_mail_template = mail.sent_template
    #         mapped_data = {
    #             **{mail.employee_id: document_mail_template}
    #         }
    #         for employee, mail_template in mapped_data.items():
    #             if not employee.email or not self.env.user.email:
    #                 continue
    #             ctx = {
    #                 'employee_to_name': employee.display_name,
    #                 'receiver_ids': employee.user_id,
    #                 'url': '/mail/view?model=%s&res_id=%s' % ('documents.share', reward.id),
    #             }
    #             RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
    #             subject = RenderMixin._render_template('Rewarded', 'documents.share', reward.ids, post_process=True)[reward.id]
    #             # body = RenderMixin._render_template(self.details, 'hr.reward', reward.ids, post_process=True)[reward.id]
    
    #             # body = """
    #             #     <div style="margin:0px;padding: 0px;">
    #             #     <p>Dear Concern,</p>
    #             #     <p>Your Employee Reward has been closed</p>
    #             #     </div>
    #             #         """
    #             body_closed = RenderMixin._render_template(self.sent_template, 'documents.share', reward.ids, post_process=True)[reward.id]
    #             body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                
    #             body = f"{body_closed}<br/>{body_sig}"
    #             # post the message
    #             matrix = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
    #             if matrix:
    #                 mailto = ','.join([email.email for email in matrix.next_user if email])
    #             matrix_cc = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', False)], limit=1)
    #             if matrix_cc:
    #                 mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
    #             attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'documents.share'), ('res_id', 'in', self.ids)])
    #             email_to_list = []
    #             email_to_list.append(self.employee_id.email)
    #             email_to_list.append(self.submit_by.email)
    #             email_to = ','.join(email_to_list)
                
    #             mail_values = {
    #                 # 'email_from': self.env.user.email_formatted,
    #                 'email_from': self.env.user.email_formatted,
    #                 'author_id': self.env.user.partner_id.id,
    #                 'model': None,
    #                 'res_id': None,
    #                 'subject': '%s reward has been approved' % employee.display_name,
    #                 'body_html': body,
    #                 'attachment_ids': attachment,
    #                 'auto_delete': True,
    #                 'email_to': email_to,
    #                 'email_cc': mailcc or '',
                
    #             }
    #             # raise UserError((mail_values['email_to']))
    #             try:
    #                 template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
    #             except ValueError:
    #                 _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
    #             else:
    #                 template_ctx = {
    #                     'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
    #                     'model_description': self.env['ir.model']._get('documents.share').display_name,
    #                     'company': self.env.company,
    #                 }
    #                 body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
    #                 mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
    #             self.env['mail.mail'].sudo().create(mail_values)#.send()

    #     return {'type': 'ir.actions.act_window_close'}


