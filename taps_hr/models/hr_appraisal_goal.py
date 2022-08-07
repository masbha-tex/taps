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
    ytd = fields.Char(string="YTD", store=True, copy=True, compute='compute_ytd')
    t_ytd = fields.Char(string="YTD", store=True, copy=True, compute='compute_target_ytd')
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

    @api.depends('t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','weight','target')
    def compute_weight(self):
        for app in self:
            if int(app.weight)>=0 and int(app.target)>=0:
                if int(app.t_apr)>=0:
                    app.write({'apr': round((int(app.weight)*app.t_apr)/app.target)})
                if int(app.t_may)>=0:
                    app.write({'may': round((int(app.weight)*app.t_may)/app.target)})
                if int(app.t_jun)>=0:
                    app.write({'jun': round((int(app.weight)*app.t_jun)/app.target)})
                if int(app.t_jul)>=0:
                    app.write({'jul': round((int(app.weight)*app.t_jul)/app.target)})
                if int(app.t_aug)>=0:
                    app.write({'aug': round((int(app.weight)*app.t_aug)/app.target)})
                if int(app.t_sep)>=0:
                    app.write({'sep': round((int(app.weight)*app.t_sep)/app.target)})
                if int(app.t_oct)>=0:
                    app.write({'oct': round((int(app.weight)*app.t_oct)/app.target)})
                if int(app.t_nov)>=0:
                    app.write({'nov': round((int(app.weight)*app.t_nov)/app.target)})
                if int(app.t_dec)>=0:
                    app.write({'dec': round((int(app.weight)*app.t_dec)/app.target)})
                if int(app.t_jan)>=0:
                    app.write({'jan': round((int(app.weight)*app.t_jan)/app.target)})
                if int(app.t_feb)>=0:
                    app.write({'feb': round((int(app.weight)*app.t_feb)/app.target)})
                if int(app.t_mar)>=0:
                    app.write({'mar': round((int(app.weight)*app.t_mar)/app.target)})
    
        
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
            s = ((int(app.apr) + int(app.may) + int(app.jun) + int(app.jul) + int(app.aug) + int(app.sep) + int(app.oct) + int(app.nov) + int(app.dec) + int(app.jan) + int(app.feb) + int(app.mar))/100)
            
            if int(app.apr)>0:
                d = d+1
            if int(app.may)>0:
                d = d+1
            if int(app.jun)>0:
                d = d+1
            if int(app.jul)>0:
                d = d+1
            if int(app.aug)>0:
                d = d+1
            if int(app.sep)>0:
                d = d+1
            if int(app.oct)>0:
                d = d+1
            if int(app.nov)>0:
                d = d+1
            if int(app.dec)>0:
                d = d+1
            if int(app.jan)>0:
                d = d+1
            if int(app.feb)>0:
                d = d+1
            if int(app.mar)>0:
                d = d+1
            if s >0:
                s = round((s/d)*100)
#             app.ytd.write = "{:.0%}".format(s)
                app.write({'ytd': s})
    
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
            t = ((app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar)/100)
            
            if app.t_apr>0:
                d = d+1
            if app.t_may>0:
                d = d+1
            if app.t_jun>0:
                d = d+1
            if app.t_jul>0:
                d = d+1
            if app.t_aug>0:
                d = d+1
            if app.t_sep>0:
                d = d+1
            if app.t_oct>0:
                d = d+1
            if app.t_nov>0:
                d = d+1
            if app.t_dec>0:
                d = d+1
            if app.t_jan>0:
                d = d+1
            if app.t_feb>0:
                d = d+1
            if app.t_mar>0:
                d = d+1
            if t >0:
                t = round((t/d)*100)
                app.write({'t_ytd': t})
    
            
              
    
