# -*- coding: utf-8 -*-new

from odoo import models, fields, api, _ 
from odoo.tools import html2plaintext, plaintext2html, is_html_empty, email_normalize
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
    issue_date = fields.Date('Issue date', readonly=True) #default=fields.Date.today()
    state = fields.Selection([
            ('draft', 'Draft'),
            ('Submit', 'Submit'),
            ('Approved', 'Approved'),
            # ('Cancel', 'Cancel'),
            ('Refused', 'Refused')], 'Status', required=True, tracking=True, default='draft')
    criteria_id = fields.Many2one('reward.criteria', required=True, string='Scope')
    title_ids = fields.Many2one('reward.title', string='Title', required=True, domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")    
    details = fields.Html('Reward For', tracking=True)

    # @api.model
    # def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
    #     if not args:
    #         args = []
    #     if name:
    #         course_ids = self._search([('name', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #         if not course_ids:
    #             course_ids = self._search([('title_ids', operator, name)] + args, limit=limit, access_rights_uid=name_get_uid)
    #     else:
    #         course_ids = self._search(args, limit=limit, access_rights_uid=name_get_uid)
    #     return course_ids #models.lazy_name_get(self.browse(course_ids).with_user(name_get_uid))

    submit_template = fields.Html('Submit Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    
                    <br>
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Reward:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Reward
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ )
    
    closed_template = fields.Html('Closed Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Your Employee Reward has been Approved</span>
                    <br>
                    <br>
                    
                    <br>
                    		
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Reward:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Reward
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ ) 

    refused_template = fields.Html('Refused Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear Concern,</span>
                    <br>
                    <span>Your Employee Reward has been Refused</span>
                    <br>
                    <br>
                    
                    <br>
                    		
                    			% if ctx.get('recipient_users'):
                    			Here is the link of your Refused:
                    			<p style="margin:16px 0px 16px 0px;">
                    				<a href="${ctx['url']}" style="margin: 0; line-height: 1.2;background-color: rgb(135, 90, 123); padding: 8px 16px; text-decoration: none; color: rgb(255, 255, 255); border-radius: 5px;" data-original-title="" title="" aria-describedby="tooltip947022">
                    		View Refused
                    	</a>
                    			</p>
                    			% endif
                    </div>
                        """ ) 

    hero_template = fields.Html('Hero Template', default=""" 
                    <div class="card" style="border-radius: 0px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); overflow: hidden; max-width: 600px; margin: 0 auto;">
                        <div class="background-image" style="background-image: url('hr_reward/static/src/img/1.png'); background-size: cover; background-position: center;color: #fff;text-align: center;">
                            <div class="container" style="padding: 25px 25px 25px 25px;">
                            <div class="border-wrapper" style="border: 2px solid #000000;border-radius: 0pxpadding: 20px;position: relative;">
                                <br/>
                                <br/>
                                <img src="hr_reward/static/src/img/logo_tex_tiny.png" alt="Company Logo" style="position: relative; width: 30%;">
                                <br/>
                                <h3 class="dear-text" style="font-size: 14px; margin-top: 50px; color: #000000;">Dear, <span style="font-size: 16px; font-weight: bold; margin-top: 50px; color: #000000;">${ctx['employee_to_name']}</span></h3>
                                <h2 class="you-text" style="font-size: 25px; font-weight: bold; margin-top: 17px; margin-bottom: 0px; color: #000000;">You Are A<br/></h2><img src="hr_reward/static/src/img/hero.png" alt="Company Logo" style="position: relative; width: 50%;"><br/>
                                <br/>
                                <div class="row">
                            <div class="col-2"></div>
                            <div class="col-8"><p style="font-size: 12px; color: #000000; text-align: center;">For ${ctx['note']}</p></div>
                            <div class="col-2"></div>
                        
                            </div>
                                <div class="content-text" style="font-size: 12px; margin-top: 10px; color: #000000;">
                                    
                                    <p>Well done, keep it up!</p>
                                    <br/>
                                    <p>Recommended by - <p style=" font-size: 12px; font-weight: bold;">${ctx['submit_by_to_name']}</p></p>
                                </div>
                                <img src="hr_reward/static/src/img/3865076.png" style="max-width: 100px; margin-left: auto; margin-right: auto; position: relative; top: 10px;">
                                <br/>
                                <br/>
                                <p style="font-size: 11px;color: #000000;">www.texfasteners.com</p>
                                <br/>
                            </div>
                        </div>
                    </div>
                        
                    </div>
                    """)

    thanku_template = fields.Html('Thank you Template', default=""" 
                    <div class="card" style="position: relative; width: 637px; height: 426px; overflow: hidden; background-image: url('hr_reward/static/src/img/th.png');  background-size: cover; color: #fff; text-align: center;padding: 30px;bottom: 0px;box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); ">
                       
                        <img src="hr_reward/static/src/img/logo_tex_tiny.png" alt="Company Logo" style="max-width: 100px; position: absolute; top: 45px; left: 500px;">
                        <p style="font-size: 12px; font-weight: bold; margin-top: 160px; color: #000000; text-align: left;  margin-left: 100px;">${ctx['employee_to_name']}</p><br/>
                        <div class="row">
                        <div class="col-7">
                        <p style="font-size: 9px; color: #000000; text-align: left; margin-left: 30px; ">${ctx['note']}</p>
                        </div>
                        </div>
                        <br/>
                        <p style="font-size: 10px; color: #000000; text-align: left;  margin-left: 50px;">Recommended by - ${ctx['submit_by_to_name']}</p>
                        <br/>
                        <br/>
                    </div>
                    """)

    kudos_template = fields.Html('Kudos Template', default=""" 
                    <div class="card" style="position: relative; width: 637px; height: 426px; overflow: hidden; background-image: url('hr_reward/static/src/img/Ku.jpg');  background-size: cover; color: #fff; text-align: center;padding: 30px;bottom: 0px;box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); ">
                       
                        <p style="font-size: 12px; font-weight: bold; margin-top: 220px; color: #000000; text-align: center;">${ctx['employee_to_name']}</p><br/>
                        <div class="row">
                            <div class="col-2"></div>
                            <div class="col-8"><p style="font-size: 9px; color: #000000; text-align: center;">${ctx['note']}</p></div>
                            <div class="col-2"></div>
                        
                        </div>
                        <br/>
                        <p style="font-size: 10px; color: #000000; text-align: center;">Recommended by - ${ctx['submit_by_to_name']}</p>
                        <br/>
                        <br/>
                    </div>
                    """)
    
    next_user = fields.Many2one('res.users', ondelete='set null', string="Next User", index=True, tracking=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments', tracking=True)

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
                subject = RenderMixin._render_template('Reward and Recognition', 'hr.reward', reward.ids, post_process=True)[reward.id]
                body = RenderMixin._render_template(self.details, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_submit = RenderMixin._render_template(self.submit_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id] 
                body = f"{body}<br/>{body_submit}<br/>{body_sig}"
                # post the message
                matrix = self.env['hr.reward.matrix'].sudo().search([('name', '=', 'MAILTO')], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.reward.matrix'].sudo().search([('name', '=', 'MAILCC')], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email])
                if matrix or matrix_cc:
                    
                    # raise UserError((self.env['hr.reward.matrix']))
                    attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
                    
                    mail_values = {
                        # 'email_from': self.env.user.email_formatted,
                        'email_from': self.submit_by.email,
                        'author_id': self.env.user.partner_id.id,
                        'model': None,
                        'res_id': None,
                        'subject': 'Raise a new reward for %s' % employee.display_name,
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
                        _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
                    else:
                        template_ctx = {
                            'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=employee.display_name)),
                            'model_description': self.env['ir.model']._get('hr.reward').display_name,
                            'company': self.env.company,
                        }
                        body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                        mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                    self.env['mail.mail'].sudo().create(mail_values)#.send()
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
        
        # raise UserError((effect)))
            
    def action_closed(self):
        # raise UserError(('goodbye'))
        if self.state == 'Submit':
            self.issue_date = fields.Date.today()
            self.state = 'Approved'
        for reward in self:
            reward_mail_template = reward.closed_template
            mapped_data = {
                **{reward.employee_id: reward_mail_template}
            }
            for employee, mail_template in mapped_data.items():
                if not employee.email or not self.env.user.email:
                    continue
                ctx = {
                    'employee_to_name': employee.name,
                    'submit_by_to_name': self.submit_by.name,
                    'recipient_users': employee.user_id,
                    'note': html2plaintext(self.details) if not is_html_empty(self.details) else '',
                    'date': self.issue_date,
                    'url': '/mail/view?model=%s&res_id=%s' % ('hr.reward', reward.id),
                    'image_url': 'hr_reward/static/src/img/logo_tex_tiny.png',
                }
                RenderMixin = self.env['mail.render.mixin'].with_context(**ctx)
                subject = RenderMixin._render_template('Rewarded', 'hr.reward', reward.ids, post_process=True)[reward.id]
                # body = RenderMixin._render_template(self.details, 'hr.reward', reward.ids, post_process=True)[reward.id]
    
                # body = """
                #     <div style="margin:0px;padding: 0px;">
                #     <p>Dear Concern,</p>
                #     <p>Your Employee Reward has been closed</p>
                #     </div>
                #         """
                body_closed = RenderMixin._render_template(self.closed_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_hero = RenderMixin._render_template(self.hero_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_thanku = RenderMixin._render_template(self.thanku_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_kudos = RenderMixin._render_template(self.kudos_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
                body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                if self.criteria_id.name == 'HERO':
                    body = f"{body_hero}<br/>{body_sig}"
                elif self.criteria_id.name == 'KUDOS':
                    body = f"{body_kudos}<br/>{body_sig}"
                elif self.criteria_id.name == 'THANK YOU':
                    body = f"{body_thanku}<br/>{body_sig}"
                # post the message
                matrix = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', employee.company_id.id)], limit=1)
                if matrix:
                    mailto = ','.join([email.email for email in matrix.next_user if email])
                matrix_cc = self.env['hr.reward.matrix'].sudo().search([('company_id', '=', False)], limit=1)
                if matrix_cc:
                    mailcc = ','.join([email.email for email in matrix_cc.next_user if email]) +','+employee.parent_id.email
                attachment = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)])
                email_to_list = []
                email_to_list.append(self.employee_id.email)
                email_to_list.append(self.submit_by.email)
                email_to = ','.join(email_to_list)
                
                mail_values = {
                    # 'email_from': self.env.user.email_formatted,
                    'email_from': self.env.user.email_formatted,
                    'author_id': self.env.user.partner_id.id,
                    'model': None,
                    'res_id': None,
                    'subject': '%s reward has been approved' % employee.display_name,
                    'body_html': body,
                    'attachment_ids': attachment,
                    'auto_delete': True,
                    'email_to': email_to,
                    'email_cc': mailcc or '',
                
                }
                # raise UserError((mail_values['email_to']))
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
                self.env['mail.mail'].sudo().create(mail_values)#.send()
      
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Reward Closed',
                'type': 'rainbow_man',
            }
        }
             
    def action_refused(self):
        if self.state == 'Submit':
            self.issue_date = fields.Date.today()
            self.state = 'Refused'
        for reward in self:
            reward_mail_template = reward.refused_template
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
                subject = RenderMixin._render_template('Refused', 'hr.reward', reward.ids, post_process=True)[reward.id]
                # body = RenderMixin._render_template(self.details, 'hr.reward', reward.ids, post_process=True)[reward.id]
    
                # body = """
                #     <div style="margin:0px;padding: 0px;">
                #     <p>Dear Concern,</p>
                #     <p>Your Employee Reward has been closed</p>
                #     </div>
                #         """
                body_closed = RenderMixin._render_template(self.refused_template, 'hr.reward', reward.ids, post_process=True)[reward.id]
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
                    'subject': '%s reward has been refused' % employee.display_name,
                    'body_html': body,
                    'attachment_ids': attachment,
                    'auto_delete': True,
                    'email_to': self.submit_by.email,
                    'email_cc': mailcc or ''
                
                }
                # raise UserError((mail_values['email_to']))
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
                self.env['mail.mail'].sudo().create(mail_values)#.send()
                
        return {
                    'effect': {
                        'fadeout': 'slow',
                        'message': 'Reward Refused',
                        # 'type': 'cancel',
                    }
                }
     

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            issue_date = vals.get('issue_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.reward', sequence_date=issue_date)
        return super(HrReward, self).create(vals)

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for reward in self:
            reward.attachment_number = attachment.get(reward.id, 0)        
        

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.reward'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'hr.reward',
            'default_res_id': self.id,
        }
        return res



class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	reward_count = fields.Integer(compute='_compute_reward_count', store=False, string='Reward')
	
	def _compute_reward_count(self):
		Reward = self.env['hr.reward']
		self.reward_count = Reward.search_count([('employee_id','=',self.id)])
