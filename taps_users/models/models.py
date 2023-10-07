# -*- coding: utf-8 -*-

from odoo import fields, models

class ResUsers(models.Model):
    _inherit = "res.users"
    
    signature = fields.Html('Email Signature', store=True, copy=True, default= """
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
    """)

