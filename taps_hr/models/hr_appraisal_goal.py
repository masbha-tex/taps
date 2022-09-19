# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError
import math


class HrAppraisalGoal(models.Model):
    _inherit = 'hr.appraisal.goal'
    
    condition = fields.Selection(selection=[
        ('less', 'Less than'),
        ('more', 'More than')], string="Improve Condition")
    month = fields.Selection(selection=[
        ('apr', 'April'),
        ('may', 'May'),
        ('jun', 'Jun'),
        ('jul', 'July'),
        ('aug', 'August'),
        ('sep', 'September'),
        ('oct', 'October'),
        ('nov', 'November'),
        ('dec', 'December'),
        ('jan', 'January'),
        ('feb', 'February'),
        ('mar', 'March'),], string="Calculate YTD")
    employee_id = fields.Many2one('hr.employee', string="Owner",
        default=lambda self: self.env.user.employee_id, required=False)
    manager_id = fields.Many2one('hr.employee', string="Challenged By", required=False)
    weight = fields.Integer(string="Weight", store=True, copy=True, default="0", required=True)
    target = fields.Float(string="Target", store=True, copy=True, default="0", required=True)
    baseline = fields.Float(string="Baseline", store=True, copy=True, default="0")
    
    ytd = fields.Float(string="Weight Total", store=True, copy=True, compute='compute_ytd')
    t_ytd = fields.Float(string="Target Total", store=True, copy=True, compute='compute_target_ytd')
    a_ytd = fields.Float(string="ACHV Total", store=True, copy=True, compute='compute_acvd_ytd')
    
    y_ytd = fields.Float(string="Weight YTD",store=True, copy=True, compute='compute_y_ytd')
    y_t_ytd = fields.Float(string="Target YTD",store=True, copy=True, compute='compute_y_target_ytd')
    y_a_ytd = fields.Float(string="ACHV YTD",store=True, copy=True, compute='compute_y_acvd_ytd')   
    
    t_apr = fields.Float('T-Apr', store=True, copy=True, default="0")
    t_may = fields.Float('T-May', store=True, copy=True, default="0")
    t_jun = fields.Float('T-Jun', store=True, copy=True, default="0")
    t_jul = fields.Float('T-Jul', store=True, copy=True, default="0")
    t_aug = fields.Float('T-Aug', store=True, copy=True, default="0")
    t_sep = fields.Float('T-Sep', store=True, copy=True, default="0")
    t_oct = fields.Float('T-Oct', store=True, copy=True, default="0")
    t_nov = fields.Float('T-Nov', store=True, copy=True, default="0")
    t_dec = fields.Float('T-Dec', store=True, copy=True, default="0")
    t_jan = fields.Float('T-Jan', store=True, copy=True, default="0")
    t_feb = fields.Float('T-Feb', store=True, copy=True, default="0")
    t_mar = fields.Float('T-Mar', store=True, copy=True, default="0")

    a_apr = fields.Float('A_Apr', store=True, copy=True, default="0")
    a_may = fields.Float('A_May', store=True, copy=True, default="0")
    a_jun = fields.Float('A_Jun', store=True, copy=True, default="0")
    a_jul = fields.Float('A_Jul', store=True, copy=True, default="0")
    a_aug = fields.Float('A_Aug', store=True, copy=True, default="0")
    a_sep = fields.Float('A_Sep', store=True, copy=True, default="0")
    a_oct = fields.Float('A_Oct', store=True, copy=True, default="0")
    a_nov = fields.Float('A_Nov', store=True, copy=True, default="0")
    a_dec = fields.Float('A_Dec', store=True, copy=True, default="0")
    a_jan = fields.Float('A_Jan', store=True, copy=True, default="0")
    a_feb = fields.Float('A_Feb', store=True, copy=True, default="0")
    a_mar = fields.Float('A_Mar', store=True, copy=True, default="0")
    
    apr = fields.Float('W-Apr', store=True, copy=True, default="0", compute='compute_weight')
    may = fields.Float('W-May', store=True, copy=True, default="0", compute='compute_weight')
    jun = fields.Float('W-Jun', store=True, copy=True, default="0", compute='compute_weight')
    jul = fields.Float('W-Jul', store=True, copy=True, default="0", compute='compute_weight')
    aug = fields.Float('W-Aug', store=True, copy=True, default="0", compute='compute_weight')
    sep = fields.Float('W-Sep', store=True, copy=True, default="0", compute='compute_weight')
    oct = fields.Float('W-Oct', store=True, copy=True, default="0", compute='compute_weight')
    nov = fields.Float('W-Nov', store=True, copy=True, default="0", compute='compute_weight')
    dec = fields.Float('W-Dec', store=True, copy=True, default="0", compute='compute_weight')
    jan = fields.Float('W-Jan', store=True, copy=True, default="0", compute='compute_weight')
    feb = fields.Float('W-Feb', store=True, copy=True, default="0", compute='compute_weight')
    mar = fields.Float('W-Mar', store=True, copy=True, default="0", compute='compute_weight')
        
    def action_confirm(self):
        self.write({'progression': '100'})

    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','weight','target','condition','month')
    def compute_weight(self):
        for app in self:
            if app.condition == 'less':
                if int(app.weight)>=0 and int(app.target)>=0:
                    if int(app.t_apr)>=0 and int(app.a_apr)>=0:
                        a = round(((app.a_apr and app.t_apr/app.a_apr)*int(app.weight))+0.01999,1)
                        if int(app.weight) < a or (int(app.t_apr) == 0 and int(app.a_apr) > 0) or (int(app.t_apr) == 0 and int(app.a_apr) == 0):
                            app.write({'apr': int(app.weight)})
                        else:
                            app.write({'apr': a})
                    if int(app.t_may)>=0 and int(app.a_may)>=0:
                        m = round(((app.a_may and app.t_may/app.a_may)*int(app.weight))+0.01999,1)
                        if int(app.weight) < m or (int(app.t_may) == 0 and int(app.a_may) > 0) or (int(app.t_may) == 0 and int(app.a_may) == 0):
                            app.write({'may': int(app.weight)})
                        else:
                            app.write({'may': m})
                    if int(app.t_jun)>=0 and int(app.a_jun)>=0:
                        j = round(((app.a_jun and app.t_jun/app.a_jun)*int(app.weight))+0.01999,1)
                        if int(app.weight) < j or (int(app.t_jun) == 0 and int(app.a_jun) > 0) or (int(app.t_jun) == 0 and int(app.a_jun) == 0):
                            app.write({'jun': int(app.weight)})
                        else:
                            app.write({'jun': j})
                    if int(app.t_jul)>=0 and int(app.a_jul)>=0:
                        jl = round(((app.a_jul and app.t_jul/app.a_jul)*int(app.weight))+0.01999,1)
                        if int(app.weight) < jl or (int(app.t_jul) == 0 and int(app.a_jul) > 0) or (int(app.t_jul) == 0 and int(app.a_jul) == 0):
                            app.write({'jul': int(app.weight)})
                        else:
                            app.write({'jul': jl})
                    if int(app.t_aug)>=0 and int(app.a_aug)>=0:
                        au = round(((app.a_aug and app.t_aug/app.a_aug)*int(app.weight))+0.01999,1)
                        if int(app.weight) < au or (int(app.t_aug) == 0 and int(app.a_aug) > 0) or (int(app.t_aug) == 0 and int(app.a_aug) == 0):
                            app.write({'aug': int(app.weight)})
                        else:
                            app.write({'aug': au})
                    if int(app.t_sep)>=0 and int(app.a_sep)>=0:
                        se = round(((app.a_sep and app.t_sep/app.a_sep)*int(app.weight))+0.01999,1)
                        if int(app.weight) < se or (int(app.t_sep) == 0 and int(app.a_sep) > 0) or (int(app.t_sep) == 0 and int(app.a_sep) == 0):
                            app.write({'sep': int(app.weight)})
                        else:
                            app.write({'sep': se})
                    if int(app.t_oct)>=0 and int(app.a_oct)>=0:
                        oc = round(((app.a_oct and app.t_oct/app.a_oct)*int(app.weight))+0.01999,1)
                        if int(app.weight) < oc or (int(app.t_oct) == 0 and int(app.a_oct) > 0) or (int(app.t_oct) == 0 and int(app.a_oct) == 0):
                            app.write({'oct': int(app.weight)})
                        else:
                            app.write({'oct': oc})
                    if int(app.t_nov)>=0 and int(app.a_nov)>=0:
                        no = round(((app.a_nov and app.t_nov/app.a_nov)*int(app.weight))+0.01999,1)
                        if int(app.weight) < no or (int(app.t_nov) == 0 and int(app.a_nov) > 0) or (int(app.t_nov) == 0 and int(app.a_nov) == 0):
                            app.write({'nov': int(app.weight)})
                        else:
                            app.write({'nov': no})
                    if int(app.t_dec)>=0 and int(app.a_dec)>=0:
                        de = round(((app.a_dec and app.t_dec/app.a_dec)*int(app.weight))+0.01999,1)
                        if int(app.weight) < de or (int(app.t_dec) == 0 and int(app.a_dec) > 0) or (int(app.t_dec) == 0 and int(app.a_dec) == 0):
                            app.write({'dec': int(app.weight)})
                        else:
                            app.write({'dec': de})
                    if int(app.t_jan)>=0 and int(app.a_jan)>=0:
                        ja = round(((app.a_jan and app.t_jan/app.a_jan)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ja or (int(app.t_jan) == 0 and int(app.a_jan) > 0) or (int(app.t_jan) == 0 and int(app.a_jan) == 0):
                            app.write({'jan': int(app.weight)})
                        else:
                            app.write({'jan': ja})
                    if int(app.t_feb)>=0 and int(app.a_feb)>=0:
                        fe = round(((app.a_feb and app.t_feb/app.a_feb)*int(app.weight))+0.01999,1)
                        if int(app.weight) < fe or (int(app.t_feb) == 0 and int(app.a_feb) > 0) or (int(app.t_feb) == 0 and int(app.a_feb) == 0):
                            app.write({'feb': int(app.weight)})
                        else:
                            app.write({'feb': fe})
                    if int(app.t_mar)>=0 and int(app.a_mar)>=0:
                        ma = round(((app.a_mar and app.t_mar/app.a_mar)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ma or (int(app.t_mar) == 0 and int(app.a_mar) > 0) or (int(app.t_mar) == 0 and int(app.a_mar) == 0):
                            app.write({'mar': int(app.weight)})
                        else:
                            app.write({'mar': ma})
            else:
                if int(app.weight)>=0 and int(app.target)>=0:
                    if int(app.t_apr)>=0 and int(app.a_apr)>=0:
                        a = round(((app.t_apr and app.a_apr/app.t_apr)*int(app.weight))+0.01999,1)
                        if int(app.weight) < a or (int(app.t_apr) == 0 and int(app.a_apr) > 0) or (int(app.t_apr) == 0 and int(app.a_apr) == 0):
                            app.write({'apr': int(app.weight)})
                        else:
                            app.write({'apr': a})
                    if int(app.t_may)>=0 and int(app.a_may)>=0:
                        m = round(((app.t_may and app.a_may/app.t_may)*int(app.weight))+0.01999,1)
                        if int(app.weight) < m or (int(app.t_may) == 0 and int(app.a_may) > 0) or (int(app.t_may) == 0 and int(app.a_may) == 0):
                            app.write({'may': int(app.weight)})
                        else:
                            app.write({'may': m})
                    if int(app.t_jun)>=0 and int(app.a_jun)>=0:
                        j = round(((app.t_jun and app.a_jun/app.t_jun)*int(app.weight))+0.01999,1)
                        if int(app.weight) < j or (int(app.t_jun) == 0 and int(app.a_jun) > 0) or (int(app.t_jun) == 0 and int(app.a_jun) == 0):
                            app.write({'jun': int(app.weight)})
                        else:
                            app.write({'jun': j})
                    if int(app.t_jul)>=0 and int(app.a_jul)>=0:
                        jl = round(((app.t_jul and app.a_jul/app.t_jul)*int(app.weight))+0.01999,1)
                        if int(app.weight) < jl or (int(app.t_jul) == 0 and int(app.a_jul) > 0) or (int(app.t_jul) == 0 and int(app.a_jul) == 0):
                            app.write({'jul': int(app.weight)})
                        else:
                            app.write({'jul': jl})
                    if int(app.t_aug)>=0 and int(app.a_aug)>=0:
                        au = round(((app.t_aug and app.a_aug/app.t_aug)*int(app.weight))+0.01999,1)
                        if int(app.weight) < au or (int(app.t_aug) == 0 and int(app.a_aug) > 0) or (int(app.t_aug) == 0 and int(app.a_aug) == 0):
                            app.write({'aug': int(app.weight)})
                        else:
                            app.write({'aug': au})
                    if int(app.t_sep)>=0 and int(app.a_sep)>=0:
                        se = round(((app.t_sep and app.a_sep/app.t_sep)*int(app.weight))+0.01999,1)
                        if int(app.weight) < se or (int(app.t_sep) == 0 and int(app.a_sep) > 0) or (int(app.t_sep) == 0 and int(app.a_sep) == 0):
                            app.write({'sep': int(app.weight)})
                        else:
                            app.write({'sep': se})
                    if int(app.t_oct)>=0 and int(app.a_oct)>=0:
                        oc = round(((app.t_oct and app.a_oct/app.t_oct)*int(app.weight))+0.01999,1)
                        if int(app.weight) < oc or (int(app.t_oct) == 0 and int(app.a_oct) > 0) or (int(app.t_oct) == 0 and int(app.a_oct) == 0):
                            app.write({'oct': int(app.weight)})
                        else:
                            app.write({'oct': oc})
                    if int(app.t_nov)>=0 and int(app.a_nov)>=0:
                        no = round(((app.t_nov and app.a_nov/app.t_nov)*int(app.weight))+0.01999,1)
                        if int(app.weight) < no or (int(app.t_nov) == 0 and int(app.a_nov) > 0) or (int(app.t_nov) == 0 and int(app.a_nov) == 0):
                            app.write({'nov': int(app.weight)})
                        else:
                            app.write({'nov': no})
                    if int(app.t_dec)>=0 and int(app.a_dec)>=0:
                        de = round(((app.t_dec and app.a_dec/app.t_dec)*int(app.weight))+0.01999,1)
                        if int(app.weight) < de or (int(app.t_dec) == 0 and int(app.a_dec) > 0) or (int(app.t_dec) == 0 and int(app.a_dec) == 0):
                            app.write({'dec': int(app.weight)})
                        else:
                            app.write({'dec': de})
                    if int(app.t_jan)>=0 and int(app.a_jan)>=0:
                        ja = round(((app.t_jan and app.a_jan/app.t_jan)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ja or (int(app.t_jan) == 0 and int(app.a_jan) > 0) or (int(app.t_jan) == 0 and int(app.a_jan) == 0):
                            app.write({'jan': int(app.weight)})
                        else:
                            app.write({'jan': ja})
                    if int(app.t_feb)>=0 and int(app.a_feb)>=0:
                        fe = round(((app.t_feb and app.a_feb/app.t_feb)*int(app.weight))+0.01999,1)
                        if int(app.weight) < fe or (int(app.t_feb) == 0 and int(app.a_feb) > 0) or (int(app.t_feb) == 0 and int(app.a_feb) == 0):
                            app.write({'feb': int(app.weight)})
                        else:
                            app.write({'feb': fe})
                    if int(app.t_mar)>=0 and int(app.a_mar)>=0:
                        ma = round(((app.t_mar and app.a_mar/app.t_mar)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ma or (int(app.t_mar) == 0 and int(app.a_mar) > 0) or (int(app.t_mar) == 0 and int(app.a_mar) == 0):
                            app.write({'mar': int(app.weight)})
                        else:
                            app.write({'mar': ma})
    
                       
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
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
                
    
    @api.depends('t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','month')
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

            t = (app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar)
            
            if t >0:
#                 t = round((t/d)*100)
                app.write({'t_ytd': round(t)})
                
    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','month')
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
                
            a = (app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar)    
                
            if a >0:
#                 a = round((a/d)*100)
                app.write({'a_ytd': round(a)})
    
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
    def compute_y_ytd(self):
        self.y_ytd = 0
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
                
            if app.month == 'apr':
                ss = app.apr
                d = 1
            elif app.month == 'may':
                ss = app.apr + app.may
                d = 1+1
            elif app.month == 'jun':
                ss = app.apr + app.may + app.jun
                d = 1+1+1
            elif app.month == 'jul':
                ss = app.apr + app.may + app.jun + app.jul
                d = 1+1+1+1
            elif app.month == 'aug':
                ss = app.apr + app.may + app.jun + app.jul + app.aug
                d = 1+1+1+1+1
            elif app.month == 'sep':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep
                d = 1+1+1+1+1+1
            elif app.month == 'oct':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct
                d = 1+1+1+1+1+1+1
            elif app.month == 'nov':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct + app.nov
                d = 1+1+1+1+1+1+1+1
            elif app.month == 'dec':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct + app.nov + app.dec
                d = 1+1+1+1+1+1+1+1+1
            elif app.month == 'jan':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct + app.nov + app.dec + app.jan
                d = 1+1+1+1+1+1+1+1+1+1
            elif app.month == 'feb':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct + app.nov + app.dec + app.jan + app.feb
                d = 1+1+1+1+1+1+1+1+1+1+1
            elif app.month == 'mar':
                ss = app.apr + app.may + app.jun + app.jul + app.aug + app.sep + app.oct + app.nov + app.dec + app.jan + app.feb + app.mar
                d = 1+1+1+1+1+1+1+1+1+1+1+1
                
            if int(app.y_t_ytd)>0 and int(app.y_a_ytd)>0:
                aaa = 0
                aaa = round((ss/(int(app.weight)*d))*int(app.weight),2)
                app.write({'y_ytd': aaa})
#                 if app.condition == 'less':
#                     s = ((int(app.y_t_ytd)/int(app.y_a_ytd))*int(app.weight))+0.01999
#                     if int(app.weight) < s:
#                         app.write({'y_ytd': int(app.weight)})
#                     else:
#                         app.write({'y_ytd': round(s)})
#                 else:
#                     s = ((int(app.y_a_ytd)/int(app.y_t_ytd))*int(app.weight))+0.01999
#                     if int(app.weight) < s:
#                         app.write({'y_ytd': int(app.weight)})
#                     else:
#                         app.write({'y_ytd': round(s)})
    
    @api.depends('t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','month')
    def compute_y_target_ytd(self):
        self.y_t_ytd = 0
        t = 0
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
            
            if app.month == 'apr':
                t = app.t_apr
            elif app.month == 'may':
                t = app.t_apr + app.t_may
            elif app.month == 'jun':
                t = app.t_apr + app.t_may + app.t_jun
            elif app.month == 'jul':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul
            elif app.month == 'aug':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug
            elif app.month == 'sep':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep
            elif app.month == 'oct':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct
            elif app.month == 'nov':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov
            elif app.month == 'dec':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec
            elif app.month == 'jan':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan
            elif app.month == 'feb':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb
            elif app.month == 'mar':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar
            if t >0:
                app.write({'y_t_ytd': round(t)})  
    
    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','month')
    def compute_y_acvd_ytd(self):
        self.y_a_ytd = 0
        a = 0
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
                
            if app.month == 'apr':
                a = app.a_apr
            elif app.month == 'may':
                a = app.a_apr + app.a_may
            elif app.month == 'jun':
                a = app.a_apr + app.a_may + app.a_jun
            elif app.month == 'jul':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul
            elif app.month == 'aug':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug
            elif app.month == 'sep':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep
            elif app.month == 'oct':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct
            elif app.month == 'nov':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov
            elif app.month == 'dec':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec
            elif app.month == 'jan':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan
            elif app.month == 'feb':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb
            elif app.month == 'mar':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar
            if a >0:
                app.write({'y_a_ytd': round(a)})                
    
            
              
    
