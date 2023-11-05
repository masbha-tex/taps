# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError


class HrReward(models.Model):
    _name = 'hr.reward'
    _description = 'Employee Reward & Recognition'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    submit_by = fields.Many2one('hr.employee',"Recommended By", required=True, default=lambda self: self.env.user.employee_id, tracking=True)
    issue_date = fields.Date('Issue date', required=True, default=fields.Date.today())
    state = fields.Selection([
            ('draft', 'Draft'),
            ('Submit', 'Submit'),
            ('Approved', 'Approved'),
            ('Cancel', 'Cancel'),
            ('Refused', 'Refused')], 'Status', required=True, tracking=True, default='draft')
    next_user = fields.Many2one('res.users', ondelete='set null', string="Next User", index=True, tracking=True)
    details = fields.Html('Reward For', tracking=True, default="""
                    <div style="margin:0px;padding: 0px;">
                    <br>
                    <br>
                    <br>                    
                    </div>
                        """)
    
    def Fs(self):
        if self.state == 'draft':
            self.state = 'Submit'
        for reward in self:
            reward_mail_template = reward.details
            mapped_data = {
                **{reward.employee_id: reward_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                # if not employee.email or not self.env.user.email:
                #     continue
                ctx = {
                    'employee_to_name': employee.display_name,
                    'recipient_users': employee.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.reward', reward.id),
                }
                sig = """
                <div style="margin:0px;padding: 0px;line-height: 1.2;">
                	<p class="MsoNormals">Regards,<o:p/>
                	</p>
                	<br>
                		<p class="MsoNormal" style="margin:0px;padding: 0px;line-height: 1.2;">
                			<b>
                				<span style="margin:0px;padding: 0px;line-height: 1.2;">${(object.employee_id.name or '')| safe}<o:p/>
                				</span>
                			</b>
                		</p>
                		<p class="MsoNormal">
                			<span style="margin:0px;padding: 0px;line-height: 1.2;">${(object.employee_id.job_id.name or '')| safe}<o:p/>
                			</span>
                		</p>
                		<p class="MsoNormal">
                			<span style="margin: 0;padding: 0px; line-height: 1.2;font-size:10.0pt;color:#1F497D;mso-ligatures:
                none">
                				<!--[if gte vml 1]><v:shapetype id="_x0000_t75" coordsize="21600,21600"
                 o:spt="75" o:preferrelative="t" path="m@4@5l@4@11@9@11@9@5xe" filled="f"
                 stroked="f">
                 <v:stroke joinstyle="miter"/>
                 <v:formulas>
                  <v:f eqn="if lineDrawn pixelLineWidth 0"/>
                  <v:f eqn="sum @0 1 0"/>
                  <v:f eqn="sum 0 0 @1"/>
                  <v:f eqn="prod @2 1 2"/>
                  <v:f eqn="prod @3 21600 pixelWidth"/>
                  <v:f eqn="prod @3 21600 pixelHeight"/>
                  <v:f eqn="sum @0 0 1"/>
                  <v:f eqn="prod @6 1 2"/>
                  <v:f eqn="prod @7 21600 pixelWidth"/>
                  <v:f eqn="sum @8 21600 0"/>
                  <v:f eqn="prod @7 21600 pixelHeight"/>
                  <v:f eqn="sum @10 21600 0"/>
                 </v:formulas>
                 <v:path o:extrusionok="f" gradientshapeok="t" o:connecttype="rect"/>
                 <o:lock v:ext="edit" aspectratio="t"/>
                </v:shapetype><v:shape id="Picture_x0020_7" o:spid="_x0000_i1025" type="#_x0000_t75"
                 alt="" style='width:46pt;height:33pt'>
                 <v:imagedata src="file:///C:/Users/ADNANA~1/AppData/Local/Temp/msohtmlclip1/01/clip_image001.png"
                  o:href="cid:image008.png@01D9F15F.259E0380"/>
                </v:shape><![endif]-->
                				<!--[if !vml]-->
                				<img width="61" height="44" src="https://taps.odoo.com/web/image/29734-c2a26318/tex%20logo%20.jpg" style="height: 0.458in; width: 0.638in;" v:shapes="Picture_x0020_7" class="" data-original-title="" title="" aria-describedby="tooltip397716" alt="">
                					<!--[endif]-->
                				</span>
                				<!--[if gte vml 1]><v:shape id="Picture_x0020_8"
                 o:spid="_x0000_i1026" type="#_x0000_t75" alt="Description: Flag Bangladesh Animated Flag Gif | Bangladesh flag, Flag gif, Bangladesh"
                 style='width:32pt;height:16.5pt;visibility:visible;mso-wrap-style:square'>
                 <v:imagedata src="file:///C:/Users/ADNANA~1/AppData/Local/Temp/msohtmlclip1/01/clip_image003.gif"
                  o:title=" Flag Bangladesh Animated Flag Gif | Bangladesh flag, Flag gif, Bangladesh"/>
                </v:shape><![endif]-->
                				<!--[if !vml]-->
                				<img width="43" height="22" src="https://media.tenor.com/n663MZEi16YAAAAC/flag-waving-flag.gif" alt="Description: Flag Bangladesh Animated Flag Gif | Bangladesh flag, Flag gif, Bangladesh" v:shapes="Picture_x0020_8" class="" style="" data-original-title="" title="" aria-describedby="tooltip361198">
                					<!--[endif]-->
                				</p>
                				<p class="MsoNormal" style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">
                					<b>
                						<span style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">
                							<a href="http://www.texfasteners.com/" style="margin: 0; line-height: 1.2;">www.texfasteners.com</a>
                						</span>
                					</b>
                				</p>
                				<p class="MsoNormal">
                					<span style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">Plot 180, 264
                &amp; 274, Adamjee EPZ, Adamjee Nagar,<o:p/>
                					</span>
                				</p>
                				<p class="MsoNormal">
                					<span style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">Siddirgonj,
                Narayngonj - 1431, Bangladesh.<o:p/>
                					</span>
                				</p>
                				<p class="MsoNormal">
                					<span style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">Office: +88 02
                997744454<o:p/>
                					</span>
                				</p>
                				<p class="MsoNormal">
                					<span style="margin: 0; line-height: 1.2;font-size: 10pt; color: black; background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">Cell:
                ${(object.employee_id.mobile or '')| safe}<o:p/>
                					</span>
                				</p>
                				<p class="MsoNormal" style="margin: 0; line-height: 1.2;">
                					<b>
                						<i>
                							<span lang="EN-GB" style="margin: 0; line-height: 1.2;font-size:10.0pt;font-family:
                				Wingdings;color:black;mso-ansi-language:EN-GB">*</span>
                						</i>
                					</b>
                					<b>
                						<i>
                							<span lang="EN-GB" style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black;mso-ansi-language:EN-GB">&nbsp;</span>
                						</i>
                					</b>
                					<b>
                						<span lang="EN-GB" style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black;mso-ansi-language:EN-GB">
                							<a href="mailto:${(object.employee_id.email or '')| safe}">
                								<span style="margin: 0; line-height: 1.2;color:black">${(object.employee_id.email or '')| safe}<o:p/></span>
                							</a>
                						</span>
                					</b>
                				</p>
                				<br>
                					<p class="MsoNormal">
                						<span lang="EN-IN" style="margin: 0; line-height: 1.2;font-size:8.0pt;font-family:&quot;Courier New&quot;;
                color:black;mso-ansi-language:EN-IN">
                							<a href="https://youtu.be/iVgAzSbYmDc" style="">
                								<b>
                									<span style="margin: 0; line-height: 1.2;font-family: Arial, sans-serif; color: black;">Check Out Our Style Story for 2023-24</span>
                								</b>
                							</a>
                							<o:p/>
                						</span>
                					</p>
                					<p/>
                					<p/>
                				</div>        
                """                
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                subject = RenderMixin._render_template(self.type.name, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body = RenderMixin._render_template(self.details, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_submit = RenderMixin._render_template(self.submit_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                body = f"{body}<br/>{body_submit}<br/>{body_sig}"
                # post the message
                matrix = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', False)], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
                
                attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
                
                mail_values = {
                    # 'email_from': self.env.user.email_formatted,
                    'email_from': self.submit_by.email,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': 'Raise a new reward against %s' % employee.display_name,
                    'body_html': body,
                    'attachment_ids': attachment,                    
                    'auto_delete': True,
                    'email_to': mailto or '',
                    'email_cc': mailcc or ''
                
                }
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                        'model_description': self.env['ir.model']._get('hr.reward').display_name,
                        'company': self.env.company,
                    }
                    # raise UserError((a))
                    body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                    mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                self.env['mail.mail'].sudo().create(mail_values).send()
                
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Submit Completed',
                'type': 'rainbow_man',
                'img_url': 'taps_grievance/static/img/success.png'
            }
        } 
            
    def action_investigation(self):
        if self.state == 'Submit':
            self.state = 'Primary Investigation'      
    def action_issue(self):
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
        if attachment:
            if self.action_taken:
                if self.state == 'Primary Investigation':
                    self.state = 'Letter Issue'
            else:
                raise UserError(('You forget to select Action To be Taken!!'))
        else:
            raise UserError(('You forget to upload Attachment!!'))   
    def action_answard(self):
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
        if len(attachment) > 1:
            if self.state == 'Letter Issue':
                self.state = 'Return Answard'
        else:
            raise UserError(('Maybe you forget to upload Return Answard Attachment!!'))                  
                   
    def action_satisfy(self):
        if self.state == 'Return Answard':
            self.state = 'Satisfactory'  
    def action_nonsatisfy(self):
        if self.state == 'Return Answard':
            self.state = 'Non-Satisfactory'
    def action_closed(self):
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
        if len(attachment) > 2:        
            if self.state == 'Satisfactory' or self.state == 'Non-Satisfactory':
                if self.final_action_taken:
                    self.state = 'Closed'
            
                    for reward in self:
                        reward_mail_template = reward.closed_template
                        mapped_data = {
                            **{reward.employee_id: reward_mail_template}
                        }
                        for employee, mail_template in mapped_data.items():
                            if not employee.email or not self.env.user.email:
                                continue
                            ctx = {
                                'employee_to_name': employee.display_name,
                                'recipient_users': employee.user_id,
                                'url': '/mail/view?model=%s&res_id=%s' % ('hr.reward', reward.id),
                            }
                            RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                            subject = RenderMixin._render_template(self.type.name, 'hr.reward', reward.ids, post_process=True)[reward.id]
                            # body = RenderMixin._render_template(self.details, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
            
                            # body = """
                            #     <div style="margin:0px;padding: 0px;">
                            #     <p>Dear Concern,</p>
                            #     <p>Your Employee Grievance has been closed</p>
                            #     </div>
                            #         """
                            body_closed = RenderMixin._render_template(self.closed_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                            body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                            
                            body = f"{body_closed}<br/>{body_sig}"
                            # post the message
                            matrix = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
                            if matrix:
                                mailto = ','.join([email.email for email in matrix.next_user if email])
                            matrix_cc = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', False)], limit=1)
                            if matrix_cc:
                                mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
                            attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
                                
                            mail_values = {
                                # 'email_from': self.env.user.email_formatted,
                                'email_from': self.env.user.email_formatted,
                                'author_id': self.env.user.partner_id.id,
                                'model': None,
                                'res_id': None,
                                'subject': '%s reward has been closed' % employee.display_name,
                                'body_html': body,
                                'attachment_ids': attachment,
                                'auto_delete': True,
                                'email_to': self.submit_by.email,
                                'email_cc': mailcc or ''
                            
                            }
                            try:
                                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                            except ValueError:
                                _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
                            else:
                                template_ctx = {
                                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                                    'model_description': self.env['ir.model']._get('hr.reward').display_name,
                                    'company': self.env.company,
                                }
                                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                            self.env['mail.mail'].sudo().create(mail_values).send()
                                 
                    return {
                        'effect': {
                            'fadeout': 'slow',
                            'message': 'reward Closed',
                            'type': 'rainbow_man',
                            'img_url': 'taps_grievance/static/img/success.png'
                        }
                    }
                else:
                    raise UserError(('You forget to select Final Action!!'))    
        else:
            raise UserError(('Maybe you forget to upload Closed Attachment!!')) 

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            issue_date = vals.get('issue_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.reward', sequence_date=issue_date)
        return super(HrReward, self).create(vals)



class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	reward_count = fields.Integer(compute='_compute_reward_count', store=False, string='Reward')
	
	def _compute_reward_count(self):
		Reward = self.env['hr.reward']
		self.reward_count = Reward.search_count([('employee_id','=',self.id)])
