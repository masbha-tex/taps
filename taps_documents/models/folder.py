from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class DocumentFolder(models.Model):
    _inherit = 'documents.folder'

    e_template = fields.Html('Sent Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Here you have been sent an access right in the workspace. Please click  below</span>
                    <br>
                    <br>
                    <br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Shared File
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )

    
    @api.model
    def create(self, vals):
        result = super(DocumentFolder, self).create(vals)
        if vals.get('group_ids'):
            # # raise UserError(folder.group_ids)
            self.folder_email(result.group_ids, None,result.id)
        if vals.get('read_group_ids'):
            # raise UserError(folder.read_group_ids)
            self.folder_email(None, result.read_group_ids,result.id)            
        return result
        
    def write(self, vals):
        gr_ids = re_ids = None
        gr_ids = self.group_ids
        re_ids = self.read_group_ids
        result = super(DocumentFolder, self).write(vals)
        
        if 'group_ids' in vals:
            groups = ','.join([str(i) for i in vals.get('group_ids')])
            groups = groups.replace('[6, False, [','').replace(']]','')
            grp_ids = [int(id_str) for id_str in groups.split(',')]
            
            recent_ids = self.env['res.groups'].browse(grp_ids)
            gr_ids = recent_ids - gr_ids
            
            if len(self) == 1:
                self.folder_email(gr_ids, None, self.id)
        if 'read_group_ids' in vals:
            groups = ','.join([str(i) for i in vals.get('read_group_ids')])
            groups = groups.replace('[6, False, [','').replace(']]','')
            r_grp_ids = [int(id_str) for id_str in groups.split(',')]
            
            recent_ids = self.env['res.groups'].browse(r_grp_ids)
            re_ids = recent_ids - re_ids
            if len(self) == 1:
                self.folder_email(None, re_ids, self.id)
        
        # if 'group_ids' in vals:
        #     if len(self) == 1:
        #         self.folder_email(gr_ids, None, self.id)

        # if 'read_group_ids' in vals:
        #     if len(self) == 1:
        #         self.folder_email(None, re_ids, self.id)

        return result
        

    def folder_email(self, group_id, read_group_id,id):
        
        # raise UserError(())
        folder_mail_template = """
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Here you have been sent an access right for this workspace. Please click  below</span>
                    <br>
                    <br>
                    <br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Shared Workspace
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """   
        employees_group_id = employees_read_group_id = employees = None
        employees_group_id = group_id
        employees_read_group_id = read_group_id
        # raise UserError((group_id))
        
        if employees_group_id:
            employees = employees_group_id
        elif employees_read_group_id:
            employees = employees_read_group_id
        
        mapped_data = {
            **{employees : folder_mail_template}
        }
        # raise UserError((mapped_data.items()))
        for employee, mail_template in mapped_data.items():
            for employee in employee:
                if not employee.users.login or not self.env.user.email:
                    return True
                # raise UserError((mail_template))
                ctx = {
                    'employee_to_name': employee.users.display_name,
                    'recipient_users': self.env.user.id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('documents.document', self.id),
                }
                
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                
                # subject = RenderMixin._render_template(folder.name, 'documents.folder', folder.ids, post_process=True)[folder.id]
                # render_result = RenderMixin._render_template(folder_mail_template, 'documents.folder', self.ids, post_process=True)
                # body = render_result.get(self.id)
                # all_doc = self.env['documents.folder'].search([])
                id_list = [id]
                # raise UserError(((id)list))
                body = RenderMixin._render_template(folder_mail_template, 'documents.folder', id_list, post_process=True)[id]
                # raise UserError((self.ids))
                # body_submit = RenderMixin._render_template(folder.e_template, 'documents.folder', folder.ids, post_process=True)[folder.id]
                # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]  
                body = f"{body}<br/>{body_sig}"
                
                mail_values = {
                    'email_from': self.env.user.email_formatted,
                    # 'email_from': self.env.user.ids.email,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    # 'subject': 'folder a documents : %s' % ', '.join([str(i.display_name) for i in sorted(folder.document_ids)]),
                    'subject': 'Give access for: %s' % self.name,
                    'body_html': body,
                    # 'attachment_ids': attachment,                    
                    'auto_delete': True,
                    'notification': True,
                    'email_to': employee.users.login,
                    # 'email_to': self.submit_by.email,
                    # 'email_cc': mailcc or '',
                
                }
                # raise UserError((mail_values['mail_values']))
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        # 'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=folder_doc_name)),
                        'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=self.name)),
                        'model_description': self.env['ir.model']._get('documents.folder').name,
                        'company': self.env.company,
                    }
                    body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                self.env['mail.mail'].sudo().create(mail_values)#.send()
    
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Mail Sent Successfully',
                'type': 'rainbow_man',
                'img_url': 'taps_grievance/static/img/success.png'
            }
        }    