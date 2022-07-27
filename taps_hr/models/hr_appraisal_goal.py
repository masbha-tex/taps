# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError


class HrAppraisalGoal(models.Model):
    _inherit = 'hr.appraisal.goal'

    ytd = fields.Char(string="YTD", store=True, copy=True, compute='compute_ytd')
    apr = fields.Char('Apr', store=True, copy=True, default="0")
    may = fields.Char('May', store=True, copy=True, default="0")
    jun = fields.Char('Jun', store=True, copy=True, default="0")
    jul = fields.Char('Jul', store=True, copy=True, default="0")
    aug = fields.Char('Aug', store=True, copy=True, default="0")
    sep = fields.Char('Sep', store=True, copy=True, default="0")
    oct = fields.Char('Oct', store=True, copy=True, default="0")
    nov = fields.Char('Nov', store=True, copy=True, default="0")
    dec = fields.Char('Dec', store=True, copy=True, default="0")
    jan = fields.Char('Jan', store=True, copy=True, default="0")
    feb = fields.Char('Feb', store=True, copy=True, default="0")
    mar = fields.Char('Mar', store=True, copy=True, default="0")
        
    def action_confirm(self):
        self.write({'progression': '100'})
        
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
            
              
    
