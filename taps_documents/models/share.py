# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import models, fields, api, exceptions
from odoo.exceptions import ValidationError, UserError
from odoo.tools.translate import _
from odoo.tools import consteq
import logging
from odoo.osv import expression

import uuid

logger = logging.getLogger("*___LMS___*")
_logger = logging.getLogger(__name__)


class DocumentShare(models.Model):
    _inherit = 'documents.share'

    receiver_ids = fields.Many2many('res.partner','documents_share_email_rel','document_ids', 'partner_id', string="Email Notify")
    email_sent = fields.Boolean('Email Sent', default=False)

    sent_template = fields.Html('Sent Template', default="""
                    <div style="margin:0px;padding: 0px;">
                    <span>Dear ${ctx['employee_to_name']},</span>
                    <br>
                    <span>Here's the document that ${ctx['user_to_name']} shared with you.</span>
                    <br>
                    % if ctx.get('validate'):
                    <span>And the file will be expired in <strong>${(object.date_deadline or '')| safe}</strong></span>
                    % endif
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

    def action_send_share_doc_by_email_cron(self):
        share_doc_ids = self.env['documents.share'].search([('email_sent', '=', False)])
        for share_doc in share_doc_ids:
            if share_doc.email_sent is False:
                share_doc.send_share_doc_mail()
                # share_doc.email_sent = True
    
    def send_share_doc_mail(self):
        for share in self:
            share_mail_template = share.sent_template
            employees = share.receiver_ids            
            mapped_data = {
                **{employees : share_mail_template}
            }
            # raise UserError((mapped_data.items()))
            for employee, mail_template in mapped_data.items():
                for employee in employee:
                    if not employee.email or not self.env.user.email:
                        return True
                    # raise UserError((employee))
                    ctx = {
                        'user_to_name': share.env.user.name,
                        'employee_to_name': employee.name,
                        'recipient_users': share.env.user.id,
                        # 'url': '/mail/view?model=%s&res_id=%s' % ('documents.share', share.id),
                        'validate': share.date_deadline,
                        'url': share.full_url,
                        
                    }
                    
            
                    sig = """
                    <div style="margin:0px;padding: 0px;">
                    	<p class="MsoNormal">Regards,<o:p/>
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
                    ${(object.employee_id.mobile or '')| safe} <o:p/>
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
                    								<span style="margin: 0; line-height: 1.2;color:black">${(object.employee_id.email or '')| safe}</span>
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
                    # subject = RenderMixin._render_template(share.name, 'documents.share', share.ids, post_process=True)[share.id]
                    body = RenderMixin._render_template(mail_template, 'documents.share', share.ids, post_process=True)[share.id]
                    # body_submit = RenderMixin._render_template(share.sent_template, 'documents.share', share.ids, post_process=True)[share.id]
                    # body_sig = RenderMixin._render_template(sig, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]
                    # raise UserError((share.id))
                    body_sig = RenderMixin._render_template(self.env.user.signature, 'res.users', self.env.user.ids, post_process=True)[self.env.user.id]  
                    body = f"{body}<br/>{body_sig}"
                    
                    mail_values = {
                        'email_from': self.env.user.email_formatted,
                        # 'email_from': self.env.user.ids.email,
                        'author_id': self.env.user.partner_id.id,
                        'model': None,
                        'res_id': None,
                        # 'subject': 'Share a documents : %s' % ', '.join([str(i.display_name) for i in sorted(share.document_ids)]),
                        'subject': '%s shared "%s" with you' % (share.env.user.name, ', '.join([str(i.display_name.replace('.pdf','')) for i in sorted(share.document_ids)])),
                        'body_html': body,
                        # 'attachment_ids': attachment,                    
                        'auto_delete': True,
                        'notification': True,
                        'email_to': employee.email,
                        # 'email_to': self.submit_by.email,
                        # 'email_cc': mailcc or '',
                    
                    }
                    # raise UserError((mail_values['mail_values']))
                    try:
                        template = self.env.ref('mail.mail_notification_light', raise_if_not_found=True)
                    except ValueError:
                        _logger.warning('QWeb template mail.mail_notification_light not found when sending reward confirmed mails. Sending without layouting.')
                    else:
                        share_doc_name = ', '.join([str(i.display_name) for i in sorted(share.document_ids) if share.document_ids])
                        template_ctx = {
                            # 'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name=share_doc_name)),
                            'message': self.env['mail.message'].sudo().new(dict(body=mail_values['body_html'], record_name='%s shared a file with you ' % share.env.user.name)),
                            'model_description': self.env['ir.model']._get('documents.share').name,
                            'company': self.env.company,
                        }
                        body = template._render(template_ctx, engine='ir.qweb', minimal_qcontext=True)
                        mail_values['body_html'] = self.env['mail.render.mixin']._replace_local_links(body)
                    send_email = self.env['mail.mail'].sudo().create(mail_values).send()
                    if send_email:
                        share.email_sent = True
        
        return {
            'effect': {
                'fadeout': 'slow',
                'message': 'Mail Sent Successfully',
                'type': 'rainbow_man',
                'img_url': 'taps_grievance/static/img/success.png'
            }
        } 

