# -*- coding: utf-8 -*-

from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"
    
    signature = fields.Html('Email Signature', store=True, copy=True, default= """
    <div style="margin:0px;padding: 0px;">
	<p class="MsoNormal" style="font-size:10.0pt;margin: 0; line-height: 1.2;">Regards,</p>
	<p></p>
	<p></p>
	<br>
		<p class="MsoNormal">
			<b>
				<span style="font-size:10.0pt;margin: 0; line-height: 1.2;">${(object.employee_id.name or '')| safe}</span>
			</b>
		</p>
		<p></p>
		<b>
                    						
                    					</b>
		<p></p>
		<p class="MsoNormal">
			<span style="margin:0;line-height: 1.2;font-size:10.0pt">${(object.employee_id.job_id.name or '')| safe}</span>
		</p>
		<p></p>
		<p></p>
		<p class="MsoNormal" style="margin: 0; line-height: 1.2;">
			<span style="margin:0;line-height: 1.2;font-size:10.0pt;color:#1F497D;mso-ligatures:
                    none">
				<!--[if !vml]-->
				<img src="https://taps.odoo.com/web/image/29734-c2a26318/tex logo .jpg" style="height: 0.458in; width: 0.638in;">
					<!--[endif]-->
				</span>
				<!--[if !vml]-->
				<img width="43" height="22" src="https://media.tenor.com/n663MZEi16YAAAAC/flag-waving-flag.gif" alt="Description: Flag Bangladesh Animated Flag Gif | Bangladesh flag, Flag gif, Bangladesh">
					<!--[endif]-->
				</p>
				<p class="MsoNormal" style="margin: 0; line-height: 1.2;font-size:10.0pt;color:black">
					<b>
						<span style="margin:0;line-height: 1.2;font-size:10.0pt;color:black">
							<a href="http://www.texfasteners.com/" style="margin: 0; line-height: 1.2;">www.texfasteners.com</a>
						</span>
					</b>
				</p>
				<p class="MsoNormal">
					<span style="margin:0;line-height: 1.2;font-size:10.0pt;color:black">Plot 180, 264
                    &amp; 274, Adamjee EPZ, Adamjee Nagar,</span>
				</p>
				<p></p>
				<p></p>
				<p class="MsoNormal">
					<span style="margin:0;line-height: 1.2;font-size:10.0pt;color:black">Siddirgonj,
                    Narayngonj - 1431, Bangladesh.</span>
				</p>
				<p></p>
				<p></p>
				<p class="MsoNormal">
					<span style="margin:0;line-height: 1.2;font-size:10.0pt;color:black">Office: +88 02
                    997744454</span>
				</p>
				<p></p>
				<p></p>
				<p class="MsoNormal">
					<span style="margin:0;line-height: 1.2;font-size: 10pt; color: black; background-image: initial; background-position: initial; background-size: initial; background-repeat: initial; background-attachment: initial; background-origin: initial; background-clip: initial;">Cell:
                    ${(object.employee_id.mobile or '')| safe} </span>
				</p>
				<p></p>
				<p></p>
				<p class="MsoNormal" style="margin: 0; line-height: 1.2;">
					<b>
						<i>
							<span lang="EN-GB" style="margin:0;line-height: 1.2;font-size:10.0pt;font-family:
                    				Wingdings;color:black;mso-ansi-language:EN-GB">*</span>
						</i>
					</b>
					<b>
						<i>
							<span lang="EN-GB" style="margin:0;line-height: 1.2;font-size:10.0pt;color:black;mso-ansi-language:EN-GB">&nbsp;</span>
						</i>
					</b>
					<b>
						<span lang="EN-GB" style="margin:0;line-height: 1.2;font-size:10.0pt;color:black;mso-ansi-language:EN-GB">
							<a href="mailto:${(object.employee_id.email or '')| safe}">
								<span style="margin:0;line-height: 1.2;color:black">${(object.employee_id.email or '')| safe}</span>
							</a>
						</span>
					</b>
				</p>
				<br>
					<p class="MsoNormal">
						<span lang="EN-IN" style="margin:0;line-height: 1.2;font-size:8.0pt;font-family:&quot;Courier New&quot;;
                    color:black;mso-ansi-language:EN-IN">
							<a href="https://youtu.be/iVgAzSbYmDc">
								<b>
									<span style="margin:0;line-height: 1.2;font-family: Arial, sans-serif; color: black;">Check Out Our Style Story for 2023-24</span>
								</b>
							</a>
						</span>
					</p>
					<p></p>
					<p></p>
					<p></p>
					<p></p>
    </div>
    """)

