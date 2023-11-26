# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class HrGrievance(models.Model):
    _name = 'hr.grievance'
    _description = 'Employee Grievance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New'))
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)    
    type = fields.Many2one('hr.grievance.type', "Type of Misconduct", help="This is the type by which the complaint was received.", tracking=True, store=True)
    action_taken = fields.Many2one('hr.grievance.action.taken', "Action to be Taken", tracking=True, help="This is the type by which the Action to be Taken was received.", store=True)
    final_action_taken = fields.Many2one('hr.grievance.final.action.taken', "Final Action", tracking=True,help="This is the type by which the Final Action was received.", store=True)
    details = fields.Html('Details of Misconduct', tracking=True, default="""
                    <div style="margin:0px;padding: 0px;">
                    <br>
                    <br>
                    <br>                    
                    </div>
                        """)
    submit_template = fields.Html('Submit Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Type of Misconduct: </span><strong>${(object.type.name or '')| safe}</strong>
                    <br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Grievance:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Grievance
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )
    closed_template = fields.Html('Closed Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Your Employee Grievance has been closed</span>
                    <br>
                    <br>
                    <span>Type of Misconduct: </span><strong>${(object.type.name or '')| safe}</strong>
                    <br>
                    		<span>Final Action: </span><strong>${(object.final_action_taken.name or '')| safe}</strong><br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Grievance:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Grievance
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )    
    
    
    submit_by = fields.Many2one('hr.employee',"Complaint By", required=True, default=lambda self: self.env.user.employee_id, tracking=True)
    state = fields.Selection([
            ('draft', 'Draft'),
            ('Submit', 'Submit'),
            ('Primary Investigation', 'Primary Investigation'),
            ('Letter Issue', 'Letter Issue'),
            ('Return Answard', 'Return Answard'),
            ('Satisfactory', 'Satisfactory'),
            ('Non-Satisfactory', 'Non-Satisfactory'),
            ('Closed', 'Closed')], 'Status', required=True, tracking=True, default='draft')
    complaint_date = fields.Date('Complaint date', required=True, default=fields.Date.today())
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments', tracking=True)
    next_user = fields.Many2one('res.users', ondelete='set null', string="Next User", index=True, tracking=True)

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
            
    @api.onchange('submit_by')
    def _onchange_submit_by(self):
        invalid_partners = self.submit_by.filtered(lambda partner: not partner.private_email)
        if invalid_partners:
            warning = {
                'title': 'Invalid "Recommended By" Email',
                'message': (("%s do not have emails. please set the emails from employee!") % invalid_partners.display_name),
            }
            self.submit_by -= invalid_partners
            return {'warning': warning}    

    def action_submit(self):
        if self.state == 'draft':
            self.state = 'Submit'
        for grievance in self:
            grievance_mail_template = grievance.details
            mapped_data = {
                **{grievance.employee_id: grievance_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                # if not employee.email or not self.env.user.email:
                #     continue
                ctx = {
                    'employee_to_name': employee.display_name,
                    'recipient_users': employee.user_id,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.grievance', grievance.id),
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
                subject = RenderMixin._render_template(self.type.name, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
                body = RenderMixin._render_template(self.details, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
                body_submit = RenderMixin._render_template(self.submit_template, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
                # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                body = f"{body}<br/>{body_submit}<br/>{body_sig}"
                # post the message
                matrix = self.env['hr.grievance.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.grievance.matrix'].sudo().search([('company_id', '=', False)], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
                
                attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)])
                
                mail_values = {
                    # 'email_from': self.env.user.email_formatted,
                    'email_from': self.submit_by.email,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': 'Raise a new grievance against %s' % employee.display_name,
                    'body_html': body,
                    'attachment_ids': attachment,                    
                    'auto_delete': True,
                    'email_to': mailto or '',
                    'email_cc': mailcc or ''
                
                }
                try:
                    template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                except ValueError:
                    _logger.warning('QWeb template mail.mail_notification_light not found when sending grievance confirmed mails. Sending without layouting.')
                else:
                    template_ctx = {
                        'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                        'model_description': self.env['ir.model']._get('hr.grievance').display_name,
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
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)])
        if attachment:
            if self.action_taken:
                if self.state == 'Primary Investigation':
                    self.state = 'Letter Issue'
            else:
                raise UserError(('You forget to select Action To be Taken!!'))
        else:
            raise UserError(('You forget to upload Attachment!!'))   
    def action_answard(self):
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)])
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
        attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)])
        if self.state == 'Submit' and len(attachment) <=1:
            self.state = 'Closed'
        elif self.state == 'Primary Investigation' and len(attachment) <=1:
            self.state = 'Closed'
        elif self.state == 'Letter Issue' and len(attachment) <=2:
            self.state = 'Closed'
        elif self.state == 'Return Answard' and len(attachment) <=3:
            self.state = 'Closed'
        elif self.state == 'Satisfactory' and len(attachment) <=3:
            self.state = 'Closed'
        elif self.state == 'Non-Satisfactory' and len(attachment) <=3:
            self.state = 'Closed'
        elif len(attachment) > 2:        
            if self.state == 'Satisfactory' or self.state == 'Non-Satisfactory':
                if self.final_action_taken:
                    self.state = 'Closed'
            
                    for grievance in self:
                        grievance_mail_template = grievance.closed_template
                        mapped_data = {
                            **{grievance.employee_id: grievance_mail_template}
                        }
                        for employee, mail_template in mapped_data.items():
                            if not employee.email or not self.env.user.email:
                                continue
                            ctx = {
                                'employee_to_name': employee.display_name,
                                'recipient_users': employee.user_id,
                                'url': '/mail/view?model=%s&res_id=%s' % ('hr.grievance', grievance.id),
                            }
                            RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                            subject = RenderMixin._render_template(self.type.name, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
                            # body = RenderMixin._render_template(self.details, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
            
                            # body = """
                            #     <div style="margin:0px;padding: 0px;">
                            #     <p>Dear Concern,</p>
                            #     <p>Your Employee Grievance has been closed</p>
                            #     </div>
                            #         """
                            body_closed = RenderMixin._render_template(self.closed_template, 'hr.grievance', grievance.ids, post_process=True)[grievance.id]
                            body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]                
                            
                            body = f"{body_closed}<br/>{body_sig}"
                            # post the message
                            matrix = self.env['hr.grievance.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
                            if matrix:
                                mailto = ','.join([email.email for email in matrix.next_user if email])
                            matrix_cc = self.env['hr.grievance.matrix'].sudo().search([('company_id', '=', False)], limit=1)
                            if matrix_cc:
                                mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
                            attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)])
                                
                            mail_values = {
                                # 'email_from': self.env.user.email_formatted,
                                'email_from': self.env.user.email_formatted,
                                'author_id': self.env.user.partner_id.id,
                                'model': None,
                                'res_id': None,
                                'subject': '%s Grievance has been closed' % employee.display_name,
                                'body_html': body,
                                'attachment_ids': attachment,
                                'auto_delete': True,
                                'email_to': self.submit_by.email,
                                'email_cc': mailcc or ''
                            
                            }
                            try:
                                template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                            except ValueError:
                                _logger.warning('QWeb template mail.mail_notification_light not found when sending grievance confirmed mails. Sending without layouting.')
                            else:
                                template_ctx = {
                                    'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                                    'model_description': self.env['ir.model']._get('hr.grievance').display_name,
                                    'company': self.env.company,
                                }
                                body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                                mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                            self.env['mail.mail'].sudo().create(mail_values).send()
                                 
                    return {
                        'effect': {
                            'fadeout': 'slow',
                            'message': 'Grievance Closed',
                            'type': 'rainbow_man',
                            'img_url': 'taps_grievance/static/img/success.png'
                        }
                    }
                else:
                    raise UserError(('You forget to select Final Action!!'))    
        else:
            raise UserError(('Maybe you forget to upload Closed Attachment!!'))                        

        # self.next_user = self.env['res.users'].search([('login','in',())])            
        # users = self.env.ref('taps_lms.group_manager_lms').users
        # for user in users:
        #     self.activity_schedule('taps_lms.mail_act_course_approval', user_id=user.id, note=f'Please Approve Training course {self.name}')
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            complaint_date = vals.get('complaint_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.grievance', sequence_date=complaint_date)
        return super(HrGrievance, self).create(vals)
        
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for grievance in self:
            grievance.attachment_number = attachment.get(grievance.id, 0)        
        

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'hr.grievance',
            'default_res_id': self.id,
        }
        return res
        
class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	grievance_count = fields.Integer(compute='_compute_grievance_count', store=False, string='Grievance')
	
	def _compute_grievance_count(self):
		Grievance = self.env['hr.grievance']
		self.grievance_count = Grievance.search_count([('employee_id','=',self.id)])
        
# class HrEmployeePublic(models.Model):
#     _inherit = 'hr.employee.public'

#     grievance_count = fields.Integer(readonly=True)