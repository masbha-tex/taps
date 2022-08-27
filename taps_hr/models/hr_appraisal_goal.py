# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError


class HrAppraisalGoal(models.Model):
    _inherit = 'hr.appraisal.goal'
    
    condition = fields.Selection(selection=[
        ('less', 'Less than'),
        ('more', 'More than')], string="Improve Condition")
    weight = fields.Integer(string="Weight", store=True, copy=True, default="0", required=True)
    target = fields.Float(string="Target", store=True, copy=True, default="0", required=True)
    baseline = fields.Float(string="Baseline", store=True, copy=True, default="0")
    ytd = fields.Char(string="Weight YTD", store=True, copy=True, compute='compute_ytd')
    t_ytd = fields.Char(string="Target YTD", store=True, copy=True, compute='compute_target_ytd')
    a_ytd = fields.Char(string="ACHV YTD", store=True, copy=True, compute='compute_acvd_ytd')    
    t_apr = fields.Float('Apr', store=True, copy=True, default="0")
    t_may = fields.Float('May', store=True, copy=True, default="0")
    t_jun = fields.Float('Jun', store=True, copy=True, default="0")
    t_jul = fields.Float('Jul', store=True, copy=True, default="0")
    t_aug = fields.Float('Aug', store=True, copy=True, default="0")
    t_sep = fields.Float('Sep', store=True, copy=True, default="0")
    t_oct = fields.Float('Oct', store=True, copy=True, default="0")
    t_nov = fields.Float('Nov', store=True, copy=True, default="0")
    t_dec = fields.Float('Dec', store=True, copy=True, default="0")
    t_jan = fields.Float('Jan', store=True, copy=True, default="0")
    t_feb = fields.Float('Feb', store=True, copy=True, default="0")
    t_mar = fields.Float('Mar', store=True, copy=True, default="0")

    a_apr = fields.Float('Apr', store=True, copy=True, default="0")
    a_may = fields.Float('May', store=True, copy=True, default="0")
    a_jun = fields.Float('Jun', store=True, copy=True, default="0")
    a_jul = fields.Float('Jul', store=True, copy=True, default="0")
    a_aug = fields.Float('Aug', store=True, copy=True, default="0")
    a_sep = fields.Float('Sep', store=True, copy=True, default="0")
    a_oct = fields.Float('Oct', store=True, copy=True, default="0")
    a_nov = fields.Float('Nov', store=True, copy=True, default="0")
    a_dec = fields.Float('Dec', store=True, copy=True, default="0")
    a_jan = fields.Float('Jan', store=True, copy=True, default="0")
    a_feb = fields.Float('Feb', store=True, copy=True, default="0")
    a_mar = fields.Float('Mar', store=True, copy=True, default="0")
    
    apr = fields.Char('Apr', store=True, copy=True, default="0", compute='compute_weight')
    may = fields.Char('May', store=True, copy=True, default="0", compute='compute_weight')
    jun = fields.Char('Jun', store=True, copy=True, default="0", compute='compute_weight')
    jul = fields.Char('Jul', store=True, copy=True, default="0", compute='compute_weight')
    aug = fields.Char('Aug', store=True, copy=True, default="0", compute='compute_weight')
    sep = fields.Char('Sep', store=True, copy=True, default="0", compute='compute_weight')
    oct = fields.Char('Oct', store=True, copy=True, default="0", compute='compute_weight')
    nov = fields.Char('Nov', store=True, copy=True, default="0", compute='compute_weight')
    dec = fields.Char('Dec', store=True, copy=True, default="0", compute='compute_weight')
    jan = fields.Char('Jan', store=True, copy=True, default="0", compute='compute_weight')
    feb = fields.Char('Feb', store=True, copy=True, default="0", compute='compute_weight')
    mar = fields.Char('Mar', store=True, copy=True, default="0", compute='compute_weight')
        
    def action_confirm(self):
        self.write({'progression': '100'})

    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','weight','target')
    def compute_weight(self):
        for app in self:
            if int(app.weight)>=0 and int(app.target)>=0:
                if int(app.t_apr)>=0 and int(app.a_apr)>=0:
                    a = round(((app.t_apr and app.a_apr/app.t_apr)*int(app.weight))+0.01999)
                    if int(app.weight) < a or (int(app.t_apr) == 0 and int(app.a_apr) > 0):
                        app.write({'apr': int(app.weight)})
                    else:
                        app.write({'apr': a})
                if int(app.t_may)>=0 and int(app.a_may)>=0:
                    m = round(((app.t_may and app.a_may/app.t_may)*int(app.weight))+0.01999)
                    if int(app.weight) < m or (int(app.t_may) == 0 and int(app.a_may) > 0):
                        app.write({'may': int(app.weight)})
                    else:
                        app.write({'may': m})
                if int(app.t_jun)>=0 and int(app.a_jun)>=0:
                    j = round(((app.t_jun and app.a_jun/app.t_jun)*int(app.weight))+0.01999)
                    if int(app.weight) < j or (int(app.t_jun) == 0 and int(app.a_jun) > 0):
                        app.write({'jun': int(app.weight)})
                    else:
                        app.write({'jun': j})
                if int(app.t_jul)>=0 and int(app.a_jul)>=0:
                    jl = round(((app.t_jul and app.a_jul/app.t_jul)*int(app.weight))+0.01999)
                    if int(app.weight) < jl or (int(app.t_jul) == 0 and int(app.a_jul) > 0):
                        app.write({'jul': int(app.weight)})
                    else:
                        app.write({'jul': jl})
                if int(app.t_aug)>=0 and int(app.a_aug)>=0:
                    au = round(((app.t_aug and app.a_aug/app.t_aug)*int(app.weight))+0.01999)
                    if int(app.weight) < au or (int(app.t_aug) == 0 and int(app.a_aug) > 0):
                        app.write({'aug': int(app.weight)})
                    else:
                        app.write({'aug': au})
                if int(app.t_sep)>=0 and int(app.a_sep)>=0:
                    se = round(((app.t_sep and app.a_sep/app.t_sep)*int(app.weight))+0.01999)
                    if int(app.weight) < se or (int(app.t_sep) == 0 and int(app.a_sep) > 0):
                        app.write({'sep': int(app.weight)})
                    else:
                        app.write({'sep': se})
                if int(app.t_oct)>=0 and int(app.a_oct)>=0:
                    oc = round(((app.t_oct and app.a_oct/app.t_oct)*int(app.weight))+0.01999)
                    if int(app.weight) < oc or (int(app.t_oct) == 0 and int(app.a_oct) > 0):
                        app.write({'oct': int(app.weight)})
                    else:
                        app.write({'oct': oc})
                if int(app.t_nov)>=0 and int(app.a_nov)>=0:
                    no = round(((app.t_nov and app.a_nov/app.t_nov)*int(app.weight))+0.01999)
                    if int(app.weight) < no or (int(app.t_nov) == 0 and int(app.a_nov) > 0):
                        app.write({'nov': int(app.weight)})
                    else:
                        app.write({'nov': no})
                if int(app.t_dec)>=0 and int(app.a_dec)>=0:
                    de = round(((app.t_dec and app.a_dec/app.t_dec)*int(app.weight))+0.01999)
                    if int(app.weight) < de or (int(app.t_dec) == 0 and int(app.a_dec) > 0):
                        app.write({'dec': int(app.weight)})
                    else:
                        app.write({'dec': de})
                if int(app.t_jan)>=0 and int(app.a_jan)>=0:
                    ja = round(((app.t_jan and app.a_jan/app.t_jan)*int(app.weight))+0.01999)
                    if int(app.weight) < ja or (int(app.t_jan) == 0 and int(app.a_jan) > 0):
                        app.write({'jan': int(app.weight)})
                    else:
                        app.write({'jan': ja})
                if int(app.t_feb)>=0 and int(app.a_feb)>=0:
                    fe = round(((app.t_feb and app.a_feb/app.t_feb)*int(app.weight))+0.01999)
                    if int(app.weight) < fe or (int(app.t_feb) == 0 and int(app.a_feb) > 0):
                        app.write({'feb': int(app.weight)})
                    else:
                        app.write({'feb': fe})
                if int(app.t_mar)>=0 and int(app.a_mar)>=0:
                    ma = round(((app.t_mar and app.a_mar/app.t_mar)*int(app.weight))+0.01999)
                    if int(app.weight) < ma or (int(app.t_mar) == 0 and int(app.a_mar) > 0):
                        app.write({'mar': int(app.weight)})
                    else:
                        app.write({'mar': ma})
    
        
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar')
    def compute_ytd(self):
        self.ytd = 0
        d = 0
        for app in self:
            if app.apr == "":
                app.apr = 0
            if app.may == "":
                app.may = 0
            if app.jun == "":
                app.jun = 0
            if app.jul == "":
                app.jul = 0
            if app.aug == "":
                app.aug = 0
            if app.sep == "":
                app.sep = 0
            if app.oct == "":
                app.oct = 0
            if app.nov == "":
                app.nov = 0
            if app.dec == "":
                app.dec = 0
            if app.jan == "":
                app.jan = 0
            if app.feb == "":
                app.feb = 0
            if app.mar == "":
                app.mar = 0
            if int(app.t_ytd)>0 and int(app.a_ytd)>0:
                s = ((int(app.a_ytd)/int(app.t_ytd))*int(app.weight))+0.01999
                if int(app.weight) < s:
                    app.write({'ytd': int(app.weight)})
                else:
                    app.write({'ytd': round(s)})
                
#                 app.write({'ytd': round(s)})                
#             s = ((int(app.apr) + int(app.may) + int(app.jun) + int(app.jul) + int(app.aug) + int(app.sep) + int(app.oct) + int(app.nov) + int(app.dec) + int(app.jan) + int(app.feb) + int(app.mar))/100)
            
#             if int(app.apr)>0:
#                 d = d+1
#             if int(app.may)>0:
#                 d = d+1
#             if int(app.jun)>0:
#                 d = d+1
#             if int(app.jul)>0:
#                 d = d+1
#             if int(app.aug)>0:
#                 d = d+1
#             if int(app.sep)>0:
#                 d = d+1
#             if int(app.oct)>0:
#                 d = d+1
#             if int(app.nov)>0:
#                 d = d+1
#             if int(app.dec)>0:
#                 d = d+1
#             if int(app.jan)>0:
#                 d = d+1
#             if int(app.feb)>0:
#                 d = d+1
#             if int(app.mar)>0:
#                 d = d+1
#             if s >0:
#                 s = round((s/d)*100)
#             app.ytd.write = "{:.0%}".format(s)
#                 app.write({'ytd': s})
    
    @api.depends('t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar')
    def compute_target_ytd(self):
        self.t_ytd = 0
        d = 0
        for app in self:
            if app.t_apr == "":
                app.t_apr = 0
            if app.t_may == "":
                app.t_may = 0
            if app.t_jun == "":
                app.t_jun = 0
            if app.t_jul == "":
                app.t_jul = 0
            if app.t_aug == "":
                app.t_aug = 0
            if app.t_sep == "":
                app.t_sep = 0
            if app.t_oct == "":
                app.t_oct = 0
            if app.t_nov == "":
                app.t_nov = 0
            if app.t_dec == "":
                app.t_dec = 0
            if app.t_jan == "":
                app.t_jan = 0
            if app.t_feb == "":
                app.t_feb = 0
            if app.t_mar == "":
                app.t_mar = 0
#             t = ((app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar)/100)
            
#             if app.t_apr>0:
#                 d = d+1
#             if app.t_may>0:
#                 d = d+1
#             if app.t_jun>0:
#                 d = d+1
#             if app.t_jul>0:
#                 d = d+1
#             if app.t_aug>0:
#                 d = d+1
#             if app.t_sep>0:
#                 d = d+1
#             if app.t_oct>0:
#                 d = d+1
#             if app.t_nov>0:
#                 d = d+1
#             if app.t_dec>0:
#                 d = d+1
#             if app.t_jan>0:
#                 d = d+1
#             if app.t_feb>0:
#                 d = d+1
#             if app.t_mar>0:
#                 d = d+1
            t = (app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar)
            
            if t >0:
#                 t = round((t/d)*100)
                app.write({'t_ytd': round(t)})
                
    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar')
    def compute_acvd_ytd(self):
        self.a_ytd = 0
        d = 0
        for app in self:
            if app.a_apr == "":
                app.a_apr = 0
            if app.a_may == "":
                app.a_may = 0
            if app.a_jun == "":
                app.a_jun = 0
            if app.a_jul == "":
                app.a_jul = 0
            if app.a_aug == "":
                app.a_aug = 0
            if app.a_sep == "":
                app.a_sep = 0
            if app.a_oct == "":
                app.a_oct = 0
            if app.a_nov == "":
                app.a_nov = 0
            if app.a_dec == "":
                app.a_dec = 0
            if app.a_jan == "":
                app.a_jan = 0
            if app.a_feb == "":
                app.a_feb = 0
            if app.a_mar == "":
                app.a_mar = 0
#             a = ((app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar)/100)
            
#             if app.a_apr>0:
#                 d = d+1
#             if app.a_may>0:
#                 d = d+1
#             if app.a_jun>0:
#                 d = d+1
#             if app.a_jul>0:
#                 d = d+1
#             if app.a_aug>0:
#                 d = d+1
#             if app.a_sep>0:
#                 d = d+1
#             if app.a_oct>0:
#                 d = d+1
#             if app.a_nov>0:
#                 d = d+1
#             if app.a_dec>0:
#                 d = d+1
#             if app.a_jan>0:
#                 d = d+1
#             if app.a_feb>0:
#                 d = d+1
#             if app.a_mar>0:
#                 d = d+1
                
            a = (app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar)    
                
            if a >0:
#                 a = round((a/d)*100)
                app.write({'a_ytd': round(a)})                
    
            
              
    