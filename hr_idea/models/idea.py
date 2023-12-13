# -*- coding: utf-8 -*-new
import subprocess, base64
import tempfile
import os
from odoo import models, fields, api, _ 
from odoo.tools import html2plaintext, plaintext2html, is_html_empty, email_normalize
from odoo.exceptions import ValidationError, UserError

class HrIdea(models.Model):
    _name = 'hr.idea'
    _description = 'Idea Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    employee_id = fields.Many2one('hr.employee', "Submit By", tracking=True, required=True, default=lambda self: self.env.user.employee_id)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    image_128 = fields.Image(related='employee_id.image_128', related_sudo=False)
    image_1920 = fields.Image(related='employee_id.image_1920', related_sudo=False)
    issue_date = fields.Date('Issue date', readonly=True) #default=fields.Date.today()
    state = fields.Selection([
            ('draft', 'Draft'),
            ('Submit', 'Submit'),
            ('Validate', 'Validate'),
            ('Refused', 'Refused')], 'Status', required=True, tracking=True, default='draft')
    criteria_id = fields.Many2one('idea.criteria', required=True, tracking=True, string='Scope')    
    details = fields.Char('Idea', size=200, tracking=True)
    # details = fields.Html('Reward For', tracking=True)
    priority = fields.Selection([
            ('1', 'Very Low'),
            ('2', 'Low'),
            ('3', 'Medium'),
            ('4', 'High'),
            ('5', 'Very High')], 'Priority', tracking=True)

    submit_template = fields.Html('Submit Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    
                    <br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link of That Idea:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Idea
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )
    
    closed_template = fields.Html('Closed Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Your Idea has been Approved</span>
                    <br>
                    <br>
                    
                    <br>
                    		
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Idea:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Idea
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ ) 

    refused_template = fields.Html('Refused Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear ${ctx['employee_to_name']},</span>
                    <br/>
                    <span>Your Idea has been Refused</span>
                    <br>
                    <br>
                    
                    <br>
                    		
                    			% if ctx.get('recipient_users'):
                    			Here is the link:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Refused
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )

    idea_template = fields.Html('Thank you Template', default=""" 
                    <div class="card" style="position: relative; width: 637px; height: 426px; overflow: hidden; background-image: url('https://taps-testing-10495661.dev.odoo.com/hr_idea/static/src/img/idea.png');  background-size: cover; color: #fff; text-align: center;padding: 30px;bottom: 0px;box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); ">
                       
                        <p style="font-size: 18px; font-weight: bold; margin-top: 250px; color: #000000; text-align: left;  margin-left: 325px;">${ctx['employee_to_name']}</p>
                        <div class="row">
                        <div class="col-7">
                        <p style="font-size: 15px; color: #0000CC; text-align: center; margin-left: 265px; margin-right:25px;">${ctx['note']}</p>
                        </div>
                        </div>
                        
                        <br/>
                    </div>
                    """)

    
    next_user = fields.Many2one('res.users', ondelete='set null', string="Next User", index=True, tracking=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments', tracking=True)

    def html_to_image(self, html_content):
        try:
            with tempfile.NamedTemporaryFile(mode='w+b', delete=False, suffix='.html') as temp_html_file:
                if isinstance(html_content, bytes):
                    temp_html_file.write(html_content)
                elif isinstance(html_content, str):
                    temp_html_file.write(html_content.encode('utf-8'))
                else:
                    raise ValueError('html_content must be either bytes or str')
                temp_html_path = temp_html_file.name
    
            # Set the output image path
            temp_image_path = os.path.join(tempfile.gettempdir(), 'output.jpeg')
    
            # Run wkhtmltoimage
            process = subprocess.Popen(
                # ['wkhtmltoimage', '--format', 'jpeg', temp_html_path, temp_image_path],
                ['wkhtmltoimage', '--format', 'jpeg', '--width', '590', temp_html_path, temp_image_path],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            _, error = process.communicate()
    
            # if process.returncode != 0:
            #     raise ValidationError(f'Error during HTML to Image conversion: {error.decode("utf-8")}')
    
            # Read the resulting image data
            with open(temp_image_path, 'rb') as image_file:
                image_data = image_file.read()
    
            # Remove temporary files
            os.remove(temp_html_path)
            os.remove(temp_image_path)
    
            return image_data
        except Exception as e:
            raise ValidationError(f'Exception during HTML to Image conversion: {str(e)}')


    @api.onchange('employee_id')
    def _onchange_employee_id(self):
        invalid_partners = self.employee_id.filtered(lambda partner: not partner.private_email)
        if invalid_partners:
            warning = {
                'title': 'Invalid "Employee" Email',
                'message': (("%s do not have emails. please set the emails from employee!") % invalid_partners.display_name),
            }
            self.employee_id -= invalid_partners
            return {'warning': warning}
                      

    
    def action_submit(self):
        if self.state == 'draft':
            self.state = 'Submit'
        for idea in self:
            idea_mail_template = idea.details
            mapped_data = {
                **{idea.employee_id: idea_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                # if not employee.email or not self.env.user.email:
                #     continue
                ctx = {
                    'employee_to_name': employee.display_name,
                    'recipient_users': employee.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.idea', idea.id),
                }

                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                subject = RenderMixin._render_template('Idea Box', 'hr.idea', idea.ids, post_process=True)[idea.id]
                body = RenderMixin._render_template(self.details, 'hr.idea', idea.ids, post_process=True)[idea.id]
                body_submit = RenderMixin._render_template(self.submit_template, 'hr.idea', idea.ids, post_process=True)[idea.id]
                
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id] 
                body = f"{body}<br/>{body_submit}<br/>{body_sig}"
                # post the message
                matrix = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILTO')], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILCC')], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email])+','+employee.parent_id.email
                if matrix or matrix_cc:
                    
                    # raise UserError((self.env['hr.idea.matrix']))
                    attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.idea'), ('res_id', 'in', self.ids)])
                    
                    mail_values = {
                        # 'email_from': self.env.user.email_formatted,
                        'email_from': self.employee_id.email,
                        'author_id': self.env.user.partner_id.id,
                        'model': None,
                        'res_id': None,
                        'subject': 'Raise a new Idea by %s' % employee.display_name,
                        'body_html': body,
                        'attachment_ids': attachment,                    
                        'auto_delete': True,
                        'email_to': mailto or '',
                        # 'email_to': self.submit_by.email,
                        'email_cc': mailcc or '',
                    
                    }
                    # raise UserError((mail_values['mail_values']))
                    try:
                        template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                    except ValueError:
                        _logger.warning('QWeb template mail.mail_notification_light not found when sending idea confirmed mails. Sending without layouting.')
                    else:
                        template_ctx = {
                            'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                            'model_description': self.env['ir.model']._get('hr.idea').display_name,
                            'company': self.env.company,
                        }
                        body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                        mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                    self.env['mail.mail'].sudo().create(mail_values).send()
                else:
                    raise UserError(('Maybe forget to add Email Matrix like..EMAILTO, EMAILCC. Please add Email Matrix in Configuration or contact with Odoo Team.'))
                
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Submit Completed',
                'type': 'rainbow_man',
                # 'img_url': 'taps_grievance/static/img/success.png'
            }
        }
        
            
    def action_closed(self):
        if self.state == 'Submit':
            self.issue_date = fields.Date.today()
            self.state = 'Validate'
        for idea in self:
            idea_mail_template = idea.closed_template
            mapped_data = {
                **{idea.employee_id: idea_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                if not employee.email or not self.env.user.email:
                    continue
                ctx = {
                    'employee_to_name': employee.name,
                    # 'submit_by_to_name': self.submit_by.name,
                    'recipient_users': employee.user_id,
                    'note': html2plaintext(self.details) if not is_html_empty(self.details) else '',
                    'date': self.issue_date,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.idea', idea.id),
                    'image_url': 'https://taps-testing-10495661.dev.odoo.com/hr_idea/static/src/img/idea.png',
                }
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                subject = RenderMixin._render_template('Rewarded', 'hr.idea', idea.ids, post_process=True)[idea.id]

                body_idea = RenderMixin._render_template(self.idea_template, 'hr.idea', idea.ids, post_process=True)[idea.id]
                # body_idea = RenderMixin._render_template(hr_idea.mail_idea_template, 'hr.idea', idea.ids, post_process=True)[idea.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
        
                

                image_data = self.html_to_image(body_idea)
                # Save the image data to a file for inspection
                # with open('/home/odoo/src/user/hr_reward/static/src/img/kudos.jpeg', 'wb') as f:
                #     f.write(image_data)
                body_idea = base64.b64encode(image_data).decode('utf-8')                    
                body = f"<img width='590' height='393' src='data:image/jpeg;base64,{body_idea}'/><br/>"                    
                # body = f"{body_idea}<br/>{body_sig}"
                
                # post the message
                matrix = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILFO')], limit=1)
                if matrix:
                    mailfo = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILCC')], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email])+','+employee.parent_id.email+','+employee.parent_id.parent_id.email
                attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.idea'), ('res_id', 'in', self.ids)])
                
                mail_values = {
                    # 'email_from': self.env.user.email_formatted,
                    'email_from': mailfo,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': 'Congratulations!! Your submitted Idea has been validated',
                    'body_html': body,
                    'attachment_ids': attachment,
                    'auto_delete': True,
                    'email_to': self.employee_id.email or '',
                    'email_cc': mailcc or '',
                
                }
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending idea confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                        'model_description': self.env['ir.model']._get('hr.idea').display_name,
                        'company': self.env.company,
                    }
                    body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                  
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                self.env['mail.mail'].sudo().create(mail_values).send()         

      
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Idea Validate',
                'type': 'rainbow_man',
            }
        }
             
    def action_refused(self):
        if self.state == 'Submit':
            self.issue_date = fields.Date.today()
            self.state = 'Refused'
        for idea in self:
            idea_mail_template = idea.refused_template
            mapped_data = {
                **{idea.employee_id: idea_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                if not employee.email or not self.env.user.email:
                    continue
                ctx = {
                    'employee_to_name': employee.name,
                    'recipient_users': employee.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.idea', idea.id),
                }
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                subject = RenderMixin._render_template('Refused', 'hr.idea', idea.ids, post_process=True)[idea.id]
                body_closed = RenderMixin._render_template(self.refused_template, 'hr.idea', idea.ids, post_process=True)[idea.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                
                body = f"{body_closed}<br/>"
                # post the message
                matrix = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILFO')], limit=1)
                if matrix:
                    mailfo = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.idea.matrix'].sudo().search([('name', '=', 'MAILCC')], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email])+','+employee.parent_id.email
                attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.idea'), ('res_id', 'in', self.ids)])
                    
                mail_values = {
                    # 'email_from': self.env.user.email_formatted,
                    'email_from': mailfo,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': 'Your submitted Idea has not been validated',
                    'body_html': body,
                    'attachment_ids': attachment,
                    'auto_delete': True,
                    'email_to': self.employee_id.email or '',
                    'email_cc': mailcc or ''
                
                }
                # raise UserError((mail_values['email_to']))
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending idea confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                        'model_description': self.env['ir.model']._get('hr.idea').display_name,
                        'company': self.env.company,
                    }
                    body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                self.env['mail.mail'].sudo().create(mail_values).send()
                
        return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'Idea Refused',
                        # 'type': 'cancel',
                    }
                }
     

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            issue_date = vals.get('issue_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.idea', sequence_date=issue_date)
        return super(HrIdea, self).create(vals)

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.idea'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for idea in self:
            idea.attachment_number = attachment.get(idea.id, 0)        
        

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.idea'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'hr.idea',
            'default_res_id': self.id,
        }
        return res



class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	idea_count = fields.Integer(compute='_compute_idea_count', store=False, string='Idea')
	
	def _compute_idea_count(self):
		Idea = self.env['hr.idea']
		self.idea_count = Idea.search_count([('employee_id','=',self.id)])

