from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class DocumentFolder(models.Model):
    _inherit = 'documents.folder'

    group_ids = fields.Many2many('res.groups',
        string="Write Groups", default=lambda self: self._get_write_group(self), help='Groups able to see the workspace and read/create/edit its documents.')
    
    @staticmethod
    def _get_write_group(self):
        res_group = False
        res_group = self.env['res.groups'].sudo().search([('category_id','=', False), ('users.id', '=', self.env.user.id)])
        
        return res_group
        
    @api.model
    def create(self, vals):
        result = super(DocumentFolder, self).create(vals)
        if vals.get('group_ids') and vals.get('read_group_ids') or vals.get('group_ids') or vals.get('read_group_ids'):
            res_group = self.env['res.groups'].sudo().search([('category_id','=', False), ('users.id', '=', self.env.user.id)])
            if not res_group in result.group_ids:
                raise UserError(('You forget to add your write access group in "Write Groups" !!'))
            self.folder_email(result.group_ids, result.read_group_ids,result.id, result.display_name)        
        return result
        
    def write(self, vals):
        gr_ids = re_ids = w_recent_ids = r_recent_ids = None
        gr_ids = self.group_ids
        re_ids = self.read_group_ids
        result = super(DocumentFolder, self).write(vals)
        res_group = self.env['res.groups'].sudo().search([('category_id','=', False), ('users.id', '=', self.env.user.id)])
        if vals.get('group_ids') and vals.get('read_group_ids'):
            # raise UserError(('folder.read_group_ids'))
            w_groups = ','.join([str(i) for i in vals.get('group_ids')])
            w_groups = w_groups.replace('[6, False, [','').replace(']]','')
            if w_groups:
                grp_ids = [int(id_str) for id_str in w_groups.split(',')]
                w_recent_ids = self.env['res.groups'].browse(grp_ids)
                if not res_group.id in grp_ids:
                    raise UserError(('You forget to add your write access group in "Write Groups" !!'))

            r_groups = ','.join([str(i) for i in vals.get('read_group_ids')])
            r_groups = r_groups.replace('[6, False, [','').replace(']]','')
            if r_groups:
                r_grp_ids = [int(id_str) for id_str in r_groups.split(',')]
                r_recent_ids = self.env['res.groups'].browse(r_grp_ids)
            if w_recent_ids:
                gr_ids = w_recent_ids - gr_ids
            else:
                gr_ids
            if r_recent_ids:
                re_ids = r_recent_ids - re_ids
            else:
                re_ids
            
            if len(self) == 1:
                self.folder_email(gr_ids, re_ids, self.id)      
                
        if vals.get('group_ids') and not vals.get('read_group_ids'):
            groups = ','.join([str(i) for i in vals.get('group_ids')])
            groups = groups.replace('[6, False, [','').replace(']]','')
            # raise UserError((groups))
            if groups:
                grp_ids = [int(id_str) for id_str in groups.split(',')]
                if not res_group.id in grp_ids:
                    raise UserError(('You forget to add your write access group in "Write Groups" !!'))
                recent_ids = self.env['res.groups'].browse(grp_ids)
                gr_ids = recent_ids - gr_ids
                if len(self) == 1:
                    self.folder_email(gr_ids, '', self.id)
                                        
        if vals.get('read_group_ids') and not vals.get('group_ids'):
            groups = ','.join([str(i) for i in vals.get('read_group_ids')])
            groups = groups.replace('[6, False, [','').replace(']]','')
            if groups:
                r_grp_ids = [int(id_str) for id_str in groups.split(',')]
                recent_ids = self.env['res.groups'].browse(r_grp_ids)
                re_ids = recent_ids - re_ids
                if len(self) == 1:
                    self.folder_email('', re_ids, self.id)

        return result
        

    def folder_email(self, group_id, read_group_id,id, f_name=None):
        
        # raise UserError(())
        folder_mail_template = """
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear ${ctx['employee_to_name']},</span>
                    <br>
                    <span>Here you have been sent an <strong>Write</strong> access for this workspace. Please click  below</span>
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
        read_folder_mail_template = """
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear ${ctx['employee_to_name']},</span>
                    <br>
                    <span>Here you have been sent an <strong>Read</strong> access for this workspace. Please click  below</span>
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
        # raise UserError((employees_group_id, employees_read_group_id))
        write_mail_template = folder_mail_template
        read_mail_template = read_folder_mail_template
        mapped_data = {
            **{read_employee: read_mail_template for read_employee in employees_read_group_id},
            **{write_employee: write_mail_template for write_employee in employees_group_id}
        }        
        # if employees_group_id:
        #     employees = employees_group_id
        # elif employees_read_group_id:
        #     employees = employees_read_group_id
        
        # mapped_data = {
        #     **{employees : folder_mail_template},
        #     **{employees : read_folder_mail_template}
        # }
        # raise UserError((mapped_data.items()))
        for employee, mail_template in mapped_data.items():
            # for employee in employee:
            
            if not employee.users.login or not self.env.user.email:
                return True
            # raise UserError((mail_template))
            ctx = {
                'employee_to_name': employee.users.display_name,
                'recipient_users': self.env.user.id,
                'url': '/mail/view?model=%s&res_id=%s' % ('documents.folder', id),
            }
            
            RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
            
            # subject = RenderMixin._render_template(folder.name, 'documents.folder', folder.ids, post_process=True)[folder.id]
            # render_result = RenderMixin._render_template(folder_mail_template, 'documents.folder', self.ids, post_process=True)
            # body = render_result.get(self.id)
            # all_doc = self.env['documents.folder'].search([])
            id_list = [id]
            # raise UserError(((id)list))
            body = ""

            # if employees_group_id:
            #     body += RenderMixin._render_template(folder_mail_template, 'documents.folder', id_list, post_process=True)[id]
            # elif employees_read_group_id:
            #     body += RenderMixin._render_template(read_folder_mail_template, 'documents.folder', id_list, post_process=True)[id]

            body += RenderMixin._render_template(mail_template, 'documents.folder', id_list, post_process=True)[id]
            
            body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id] 
            body = f"{body}<br/>{body_sig}"
            # if employees_group_id == True:
            #     body = RenderMixin._render_template(folder_mail_template, 'documents.folder', id_list, post_process=True)[id]
            # if employees_read_group_id == True:
            #     body = RenderMixin._render_template(read_folder_mail_template, 'documents.folder', id_list, post_process=True)[id]
            # raise UserError((self.ids))
            # body_submit = RenderMixin._render_template(folder.e_template, 'documents.folder', folder.ids, post_process=True)[folder.id]
            # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
            # body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]  
            # body = f"{body}<br/>{body_sig}"


            
            mail_values = {
                'email_from': self.env.user.email_formatted,
                # 'email_from': self.env.user.ids.email,
                'author_id': self.env.user.partner_id.id,
                'model': None,
                'res_id': None,
                # 'subject': 'folder a documents : %s' % ', '.join([str(i.display_name) for i in sorted(folder.document_ids)]),
                'subject': '%s has invited you to "%s"' % (self.env.user.name, f_name or self.display_name),
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
                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=f_name or self.display_name)),
                    'model_description': self.env['ir.model']._get('documents.folder').name,
                    'company': self.env.company,
                }
                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
            self.env['mail.mail'].sudo().create(mail_values).send()   