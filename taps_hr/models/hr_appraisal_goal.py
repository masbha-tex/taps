# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api
from odoo.exceptions import UserError
import math


class HrAppraisalGoal(models.Model):
    _inherit = 'hr.appraisal.goal'
    _order = 'sequence'
    
    condition = fields.Selection(selection=[
        ('less', 'Less than'),
        ('more', 'More than')], string="Improve Condition", tracking=True)
    calculate = fields.Selection(selection=[
        ('sum', 'Sum'),
        ('avg', 'AVG')], string="Calculate", default="sum")    
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
    sequence = fields.Integer(default=10)    
    employee_id = fields.Many2one('hr.employee', string="Owner",
        default=lambda self: self.env.user.employee_id, required=False, tracking=True)
    manager_id = fields.Many2one('hr.employee', string="Challenged By", required=False, tracking=True)
    weight = fields.Integer(string="Weight", store=True, copy=True, default="0", required=True, tracking=True)
    target = fields.Float(string="Target", store=True, copy=True, default="0", required=True, tracking=True)
    baseline = fields.Float(string="Baseline", store=True, copy=True, default="0", tracking=True)
    
    ytd = fields.Float(string="Weight Total", store=True, copy=True, compute='compute_ytd')
    t_ytd = fields.Float(string="Target Total", store=True, copy=True, compute='compute_target_ytd')
    a_ytd = fields.Float(string="ACHV Total", store=True, copy=True, compute='compute_acvd_ytd')
    
    q_1_ytd = fields.Float(string="Q1",store=True, copy=True, compute='compute_q_1_ytd')
    q_2_ytd = fields.Float(string="Q2",store=True, copy=True, compute='compute_q_2_ytd')
    q_3_ytd = fields.Float(string="Q3",store=True, copy=True, compute='compute_q_3_ytd')
    q_4_ytd = fields.Float(string="Q4",store=True, copy=True, compute='compute_q_4_ytd') 
    
    y_ytd = fields.Float(string="Weight YTD",store=True, copy=True, compute='compute_y_ytd')
    y_t_ytd = fields.Float(string="Target YTD",store=True, copy=True, compute='compute_y_target_ytd')
    y_a_ytd = fields.Float(string="ACHV YTD",store=True, copy=True, compute='compute_y_acvd_ytd')   
    
    t_apr = fields.Float('T-Apr', store=True, copy=True, default="0", tracking=True)
    t_may = fields.Float('T-May', store=True, copy=True, default="0", tracking=True)
    t_jun = fields.Float('T-Jun', store=True, copy=True, default="0", tracking=True)
    t_q1 = fields.Float('T-Q1', store=True, copy=True, default="0", compute='compute_q_1_ytd')
    t_jul = fields.Float('T-Jul', store=True, copy=True, default="0", tracking=True)
    t_aug = fields.Float('T-Aug', store=True, copy=True, default="0", tracking=True)
    t_sep = fields.Float('T-Sep', store=True, copy=True, default="0", tracking=True)
    t_q2 = fields.Float('T-Q2', store=True, copy=True, default="0", compute='compute_q_2_ytd')
    t_oct = fields.Float('T-Oct', store=True, copy=True, default="0", tracking=True)
    t_nov = fields.Float('T-Nov', store=True, copy=True, default="0", tracking=True)
    t_dec = fields.Float('T-Dec', store=True, copy=True, default="0", tracking=True)
    t_q3 = fields.Float('T-Q3', store=True, copy=True, default="0", compute='compute_q_3_ytd')
    t_jan = fields.Float('T-Jan', store=True, copy=True, default="0", tracking=True)
    t_feb = fields.Float('T-Feb', store=True, copy=True, default="0", tracking=True)
    t_mar = fields.Float('T-Mar', store=True, copy=True, default="0", tracking=True)
    t_q4 = fields.Float('T-Q4', store=True, copy=True, default="0", compute='compute_q_4_ytd')

    a_apr = fields.Float('A_Apr', store=True, copy=True, default="0", tracking=True)
    a_may = fields.Float('A_May', store=True, copy=True, default="0", tracking=True)
    a_jun = fields.Float('A_Jun', store=True, copy=True, default="0", tracking=True)
    a_q1 = fields.Float('A_Q1', store=True, copy=True, default="0", compute='compute_q_1_ytd')
    a_jul = fields.Float('A_Jul', store=True, copy=True, default="0", tracking=True)
    a_aug = fields.Float('A_Aug', store=True, copy=True, default="0", tracking=True)
    a_sep = fields.Float('A_Sep', store=True, copy=True, default="0", tracking=True)
    a_q2 = fields.Float('A_Q2', store=True, copy=True, default="0", compute='compute_q_2_ytd')
    a_oct = fields.Float('A_Oct', store=True, copy=True, default="0", tracking=True)
    a_nov = fields.Float('A_Nov', store=True, copy=True, default="0", tracking=True)
    a_dec = fields.Float('A_Dec', store=True, copy=True, default="0", tracking=True)
    a_q3 = fields.Float('A_Q3', store=True, copy=True, default="0", compute='compute_q_3_ytd')
    a_jan = fields.Float('A_Jan', store=True, copy=True, default="0", tracking=True)
    a_feb = fields.Float('A_Feb', store=True, copy=True, default="0", tracking=True)
    a_mar = fields.Float('A_Mar', store=True, copy=True, default="0", tracking=True)
    a_q4 = fields.Float('A_Q4', store=True, copy=True, default="0", compute='compute_q_4_ytd')
    
    apr = fields.Float('W-Apr', store=True, copy=True, default="0", compute='compute_weight')
    may = fields.Float('W-May', store=True, copy=True, default="0", compute='compute_weight')
    jun = fields.Float('W-Jun', store=True, copy=True, default="0", compute='compute_weight')
    q1 = fields.Float('W-Q1', store=True, default="0", copy=True, compute='compute_q_1_ytd')
    jul = fields.Float('W-Jul', store=True, copy=True, default="0", compute='compute_weight')
    aug = fields.Float('W-Aug', store=True, copy=True, default="0", compute='compute_weight')
    sep = fields.Float('W-Sep', store=True, copy=True, default="0", compute='compute_weight')
    q2 = fields.Float('W-Q2', store=True, default="0", copy=True, compute='compute_q_2_ytd')
    oct = fields.Float('W-Oct', store=True, copy=True, default="0", compute='compute_weight')
    nov = fields.Float('W-Nov', store=True, copy=True, default="0", compute='compute_weight')
    dec = fields.Float('W-Dec', store=True, copy=True, default="0", compute='compute_weight')
    q3 = fields.Float('W-Q3', store=True, default="0", copy=True, compute='compute_q_3_ytd')
    jan = fields.Float('W-Jan', store=True, copy=True, default="0", compute='compute_weight')
    feb = fields.Float('W-Feb', store=True, copy=True, default="0", compute='compute_weight')
    mar = fields.Float('W-Mar', store=True, copy=True, default="0", compute='compute_weight')
    q4 = fields.Float('W-Q4', store=True, default="0", copy=True, compute='compute_q_4_ytd')

    apr_k = fields.Float('K-Apr', store=True, copy=True, default="0", compute='compute_kpi_achv')
    may_k = fields.Float('K-May', store=True, copy=True, default="0", compute='compute_kpi_achv')
    jun_k = fields.Float('K-Jun', store=True, copy=True, default="0", compute='compute_kpi_achv')
    q1_k = fields.Float('K-Q1', store=True, default="0", copy=True, compute='compute_kpi_achv')
    jul_k = fields.Float('K-Jul', store=True, copy=True, default="0", compute='compute_kpi_achv')
    aug_k = fields.Float('K-Aug', store=True, copy=True, default="0", compute='compute_kpi_achv')
    sep_k = fields.Float('K-Sep', store=True, copy=True, default="0", compute='compute_kpi_achv')
    q2_k = fields.Float('K-Q2', store=True, default="0", copy=True, compute='compute_kpi_achv')
    oct_k = fields.Float('K-Oct', store=True, copy=True, default="0", compute='compute_kpi_achv')
    nov_k = fields.Float('K-Nov', store=True, copy=True, default="0", compute='compute_kpi_achv')
    dec_k = fields.Float('K-Dec', store=True, copy=True, default="0", compute='compute_kpi_achv')
    q3_k = fields.Float('K-Q3', store=True, default="0", copy=True, compute='compute_kpi_achv')
    jan_k = fields.Float('K-Jan', store=True, copy=True, default="0", compute='compute_kpi_achv')
    feb_k = fields.Float('K-Feb', store=True, copy=True, default="0", compute='compute_kpi_achv')
    mar_k = fields.Float('K-Mar', store=True, copy=True, default="0", compute='compute_kpi_achv')
    q4_k = fields.Float('K-Q4', store=True, default="0", copy=True, compute='compute_kpi_achv')
    ytd_k = fields.Float(string="KPI ACHV Total", store=True, copy=True, compute='compute_kpi_achv')
    state = fields.Selection([
    ('draft', 'To Submit'),
    ('submit', 'Submitted'),
    ('approved', 'Approved'),
    ('refused', 'Refused')], string='Status', copy=False, 
        index=True, readonly=True, store=True, default='draft', tracking=False, help="Status of the Goal")
    active = fields.Boolean('Active', default=True, tracking=True)
  
    
    def action_confirm(self):
        self.write({'progression': '100'})

    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','weight','target','condition','month')
    def compute_weight(self):
        for app in self:
            if app.condition == 'less':
                if int(app.weight)>=0 and int(app.target)>=0:
                    if int(app.t_apr)>=0:
                        a = round(((app.a_apr and app.t_apr/app.a_apr)*int(app.weight))+0.01999,1)
                        if int(app.weight) < a or (int(app.t_apr) == 0 and int(app.a_apr) < 0) or (int(app.t_apr) == 0 and int(app.a_apr) == 0):
                            app.write({'apr': int(app.weight)})
                            
                        else:
                            app.write({'apr': a})
                    if int(app.t_may)>=0:
                        m = round(((app.a_may and app.t_may/app.a_may)*int(app.weight))+0.01999,1)
                        if int(app.weight) < m or (int(app.t_may) == 0 and int(app.a_may) < 0) or (int(app.t_may) == 0 and int(app.a_may) == 0):
                            app.write({'may': int(app.weight)})
                        else:
                            app.write({'may': m})
                    if int(app.t_jun)>=0:
                        j = round(((app.a_jun and app.t_jun/app.a_jun)*int(app.weight))+0.01999,1)
                        if int(app.weight) < j or (int(app.t_jun) == 0 and int(app.a_jun) < 0) or (int(app.t_jun) == 0 and int(app.a_jun) == 0):
                            app.write({'jun': int(app.weight)})
                        else:
                            app.write({'jun': j})
                    if int(app.t_jul)>=0:
                        jl = round(((app.a_jul and app.t_jul/app.a_jul)*int(app.weight))+0.01999,1)
                        if int(app.weight) < jl or (int(app.t_jul) == 0 and int(app.a_jul) < 0) or (int(app.t_jul) == 0 and int(app.a_jul) == 0):
                            app.write({'jul': int(app.weight)})
                        else:
                            app.write({'jul': jl})
                    if int(app.t_aug)>=0:
                        au = round(((app.a_aug and app.t_aug/app.a_aug)*int(app.weight))+0.01999,1)
                        if int(app.weight) < au or (int(app.t_aug) == 0 and int(app.a_aug) < 0) or (int(app.t_aug) == 0 and int(app.a_aug) == 0):
                            app.write({'aug': int(app.weight)})
                        else:
                            app.write({'aug': au})
                    if int(app.t_sep)>=0 :
                        se = round(((app.a_sep and app.t_sep/app.a_sep)*int(app.weight))+0.01999,1)
                        if int(app.weight) < se or (int(app.t_sep) == 0 and int(app.a_sep) < 0) or (int(app.t_sep) == 0 and int(app.a_sep) == 0):
                            app.write({'sep': int(app.weight)})
                        else:
                            app.write({'sep': se})
                    if int(app.t_oct)>=0:
                        oc = round(((app.a_oct and app.t_oct/app.a_oct)*int(app.weight))+0.01999,1)
                        if int(app.weight) < oc or (int(app.t_oct) == 0 and int(app.a_oct) < 0) or (int(app.t_oct) == 0 and int(app.a_oct) == 0):
                            app.write({'oct': int(app.weight)})
                        else:
                            app.write({'oct': oc})
                    if int(app.t_nov)>=0:
                        no = round(((app.a_nov and app.t_nov/app.a_nov)*int(app.weight))+0.01999,1)
                        if int(app.weight) < no or (int(app.t_nov) == 0 and int(app.a_nov) < 0) or (int(app.t_nov) == 0 and int(app.a_nov) == 0):
                            app.write({'nov': int(app.weight)})
                        else:
                            app.write({'nov': no})
                    if int(app.t_dec)>=0:
                        de = round(((app.a_dec and app.t_dec/app.a_dec)*int(app.weight))+0.01999,1)
                        if int(app.weight) < de or (int(app.t_dec) == 0 and int(app.a_dec) < 0) or (int(app.t_dec) == 0 and int(app.a_dec) == 0):
                            app.write({'dec': int(app.weight)})
                        else:
                            app.write({'dec': de})
                    if int(app.t_jan)>=0:
                        ja = round(((app.a_jan and app.t_jan/app.a_jan)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ja or (int(app.t_jan) == 0 and int(app.a_jan) < 0) or (int(app.t_jan) == 0 and int(app.a_jan) == 0):
                            app.write({'jan': int(app.weight)})
                        else:
                            app.write({'jan': ja})
                    if int(app.t_feb)>=0:
                        fe = round(((app.a_feb and app.t_feb/app.a_feb)*int(app.weight))+0.01999,1)
                        if int(app.weight) < fe or (int(app.t_feb) == 0 and int(app.a_feb) < 0) or (int(app.t_feb) == 0 and int(app.a_feb) == 0):
                            app.write({'feb': int(app.weight)})
                        else:
                            app.write({'feb': fe})
                    if int(app.t_mar)>=0:
                        ma = round(((app.a_mar and app.t_mar/app.a_mar)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ma or (int(app.t_mar) == 0 and int(app.a_mar) < 0) or (int(app.t_mar) == 0 and int(app.a_mar) == 0):
                            app.write({'mar': int(app.weight)})
                        else:
                            app.write({'mar': ma})
            else:
                if int(app.weight)>=0 and int(app.target)>=0:
                    if int(app.t_apr)>=0:
                        a = round(((app.t_apr and app.a_apr/app.t_apr)*int(app.weight))+0.01999,1)
                        if int(app.weight) < a or (int(app.t_apr) == 0 and int(app.a_apr) > 0) or (int(app.t_apr) == 0 and int(app.a_apr) == 0):
                            app.write({'apr': int(app.weight)})
                        else:
                            app.write({'apr': a})
                    if int(app.t_may)>=0:
                        m = round(((app.t_may and app.a_may/app.t_may)*int(app.weight))+0.01999,1)
                        if int(app.weight) < m or (int(app.t_may) == 0 and int(app.a_may) > 0) or (int(app.t_may) == 0 and int(app.a_may) == 0):
                            app.write({'may': int(app.weight)})
                        else:
                            app.write({'may': m})
                    if int(app.t_jun)>=0:
                        j = round(((app.t_jun and app.a_jun/app.t_jun)*int(app.weight))+0.01999,1)
                        if int(app.weight) < j or (int(app.t_jun) == 0 and int(app.a_jun) > 0) or (int(app.t_jun) == 0 and int(app.a_jun) == 0):
                            app.write({'jun': int(app.weight)})
                        else:
                            app.write({'jun': j})
                    if int(app.t_jul)>=0:
                        jl = round(((app.t_jul and app.a_jul/app.t_jul)*int(app.weight))+0.01999,1)
                        if int(app.weight) < jl or (int(app.t_jul) == 0 and int(app.a_jul) > 0) or (int(app.t_jul) == 0 and int(app.a_jul) == 0):
                            app.write({'jul': int(app.weight)})
                        else:
                            app.write({'jul': jl})
                    if int(app.t_aug)>=0:
                        au = round(((app.t_aug and app.a_aug/app.t_aug)*int(app.weight))+0.01999,1)
                        if int(app.weight) < au or (int(app.t_aug) == 0 and int(app.a_aug) > 0) or (int(app.t_aug) == 0 and int(app.a_aug) == 0):
                            app.write({'aug': int(app.weight)})
                        else:
                            app.write({'aug': au})
                    if int(app.t_sep)>=0:
                        se = round(((app.t_sep and app.a_sep/app.t_sep)*int(app.weight))+0.01999,1)
                        if int(app.weight) < se or (int(app.t_sep) == 0 and int(app.a_sep) > 0) or (int(app.t_sep) == 0 and int(app.a_sep) == 0):
                            app.write({'sep': int(app.weight)})
                        else:
                            app.write({'sep': se})
                    if int(app.t_oct)>=0:
                        oc = round(((app.t_oct and app.a_oct/app.t_oct)*int(app.weight))+0.01999,1)
                        if int(app.weight) < oc or (int(app.t_oct) == 0 and int(app.a_oct) > 0) or (int(app.t_oct) == 0 and int(app.a_oct) == 0):
                            app.write({'oct': int(app.weight)})
                        else:
                            app.write({'oct': oc})
                    if int(app.t_nov)>=0:
                        no = round(((app.t_nov and app.a_nov/app.t_nov)*int(app.weight))+0.01999,1)
                        if int(app.weight) < no or (int(app.t_nov) == 0 and int(app.a_nov) > 0) or (int(app.t_nov) == 0 and int(app.a_nov) == 0):
                            app.write({'nov': int(app.weight)})
                        else:
                            app.write({'nov': no})
                    if int(app.t_dec)>=0:
                        de = round(((app.t_dec and app.a_dec/app.t_dec)*int(app.weight))+0.01999,1)
                        if int(app.weight) < de or (int(app.t_dec) == 0 and int(app.a_dec) > 0) or (int(app.t_dec) == 0 and int(app.a_dec) == 0):
                            app.write({'dec': int(app.weight)})
                        else:
                            app.write({'dec': de})
                    if int(app.t_jan)>=0:
                        ja = round(((app.t_jan and app.a_jan/app.t_jan)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ja or (int(app.t_jan) == 0 and int(app.a_jan) > 0) or (int(app.t_jan) == 0 and int(app.a_jan) == 0):
                            app.write({'jan': int(app.weight)})
                        else:
                            app.write({'jan': ja})
                    if int(app.t_feb)>=0:
                        fe = round(((app.t_feb and app.a_feb/app.t_feb)*int(app.weight))+0.01999,1)
                        if int(app.weight) < fe or (int(app.t_feb) == 0 and int(app.a_feb) > 0) or (int(app.t_feb) == 0 and int(app.a_feb) == 0):
                            app.write({'feb': int(app.weight)})
                        else:
                            app.write({'feb': fe})
                    if int(app.t_mar)>=0:
                        ma = round(((app.t_mar and app.a_mar/app.t_mar)*int(app.weight))+0.01999,1)
                        if int(app.weight) < ma or (int(app.t_mar) == 0 and int(app.a_mar) > 0) or (int(app.t_mar) == 0 and int(app.a_mar) == 0):
                            app.write({'mar': int(app.weight)})
                        else:
                            app.write({'mar': ma})
            if app.month == 'apr':
                app.write({'may':False, 'jun':False, 'jul':False, 'aug':False, 'sep':False, 'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'may':
                app.write({'jun':False, 'jul':False, 'aug':False, 'sep':False, 'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'jun':
                app.write({'jul':False, 'aug':False, 'sep':False, 'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'jul':
                app.write({'aug':False, 'sep':False, 'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'aug':
                app.write({'sep':False, 'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'sep':
                app.write({'oct':False, 'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'oct':
                app.write({'nov':False, 'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'nov':
                app.write({'dec':False, 'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'dec':
                app.write({'jan':False, 'feb':False, 'mar':False })
            elif app.month == 'jan':
                app.write({'feb':False, 'mar':False })
            elif app.month == 'feb':
                app.write({'mar':False })        
    
                       
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
    def compute_ytd(self):
        self.ytd = 0
        s = 0
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

            t = (app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar)
            
            if t >0:
#                 t = round((t/d)*100)
                app.write({'t_ytd': round(t)})
                
    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','month')
    def compute_acvd_ytd(self):
        self.a_ytd = 0
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
                
            a = (app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar)    
                
            if a >0:
#                 a = round((a/d)*100)
                app.write({'a_ytd': round(a)})
    
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
    def compute_y_ytd(self):
        self.y_ytd = 0
        aaa = 0
        ss = 0
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
                
            if ss>0:
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
    
    @api.depends('t_apr','t_may','t_jun','t_jul','t_aug','t_sep','t_oct','t_nov','t_dec','t_jan','t_feb','t_mar','month','calculate')
    def compute_y_target_ytd(self):
        self.y_t_ytd = 0
        t = 0
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
            
            if app.month == 'apr':
                t = app.t_apr
                d = 1
            elif app.month == 'may':
                t = app.t_apr + app.t_may
                d = 1+1
            elif app.month == 'jun':
                t = app.t_apr + app.t_may + app.t_jun
                d = 1+1+1
            elif app.month == 'jul':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul
                d = 1+1+1+1
            elif app.month == 'aug':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug
                d = 1+1+1+1+1
            elif app.month == 'sep':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep
                d = 1+1+1+1+1+1
            elif app.month == 'oct':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct
                d = 1+1+1+1+1+1+1
            elif app.month == 'nov':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov
                d = 1+1+1+1+1+1+1+1
            elif app.month == 'dec':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec
                d = 1+1+1+1+1+1+1+1+1
            elif app.month == 'jan':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan
                d = 1+1+1+1+1+1+1+1+1+1
            elif app.month == 'feb':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb
                d = 1+1+1+1+1+1+1+1+1+1+1
            elif app.month == 'mar':
                t = app.t_apr + app.t_may + app.t_jun + app.t_jul + app.t_aug + app.t_sep + app.t_oct + app.t_nov + app.t_dec + app.t_jan + app.t_feb + app.t_mar
                d = 1+1+1+1+1+1+1+1+1+1+1+1
            if t >0:
                if app.calculate == 'avg':
                    app.write({'y_t_ytd': round((t/d),2)})
                else:
                    app.write({'y_t_ytd': round(t,2)})  
    
    @api.depends('a_apr','a_may','a_jun','a_jul','a_aug','a_sep','a_oct','a_nov','a_dec','a_jan','a_feb','a_mar','month','calculate')
    def compute_y_acvd_ytd(self):
        self.y_a_ytd = 0
        a = 0
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
                
            if app.month == 'apr':
                a = app.a_apr
                d = 1
            elif app.month == 'may':
                a = app.a_apr + app.a_may
                d = 1+1
            elif app.month == 'jun':
                a = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'jul':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul
                d = 1+1+1+1
            elif app.month == 'aug':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug
                d = 1+1+1+1+1
            elif app.month == 'sep':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1+1+1+1
            elif app.month == 'oct':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct
                d = 1+1+1+1+1+1+1
            elif app.month == 'nov':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov
                d = 1+1+1+1+1+1+1+1
            elif app.month == 'dec':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec
                d = 1+1+1+1+1+1+1+1+1
            elif app.month == 'jan':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan
                d = 1+1+1+1+1+1+1+1+1+1
            elif app.month == 'feb':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb
                d = 1+1+1+1+1+1+1+1+1+1+1
            elif app.month == 'mar':
                a = app.a_apr + app.a_may + app.a_jun + app.a_jul + app.a_aug + app.a_sep + app.a_oct + app.a_nov + app.a_dec + app.a_jan + app.a_feb + app.a_mar
                d = 1+1+1+1+1+1+1+1+1+1+1+1
            if a >0:
                if app.calculate == 'avg':
                    app.write({'y_a_ytd': round((a/d),2)})
                else:
                    app.write({'y_a_ytd': round(a,2)})                
    
    @api.depends('apr','may','jun','jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
    def compute_q_1_ytd(self):
        self.q_1_ytd = 0
        aaa = 0
        ss = 0
        tt = 0
        aa = 0
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
                tt = app.t_apr
                aa = app.a_apr
                d = 1
            elif app.month == 'may':
                ss = app.apr + app.may
                tt = app.t_apr + app.t_may
                aa = app.a_apr + app.a_may
                d = 1+1
            elif app.month == 'jun':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'jul':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'aug':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'sep':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'oct':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'nov':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'dec':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'jan':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'feb':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
            elif app.month == 'mar':
                ss = app.apr + app.may + app.jun
                tt = app.t_apr + app.t_may + app.t_jun
                aa = app.a_apr + app.a_may + app.a_jun
                d = 1+1+1
                
            if ss>0:
                aaa = round((ss/(int(app.weight)*d))*int(app.weight),2)
                app.write({'q_1_ytd': aaa,
                           'q1': aaa})
            if tt >0:
                if app.calculate == 'avg':
                    app.write({'t_q1': round((tt/d),2)})
                else:
                    app.write({'t_q1': round(tt,2)})  
            if aa >0:
                if app.calculate == 'avg':
                    app.write({'a_q1': round((aa/d),2)})
                else:
                    app.write({'a_q1': round(aa,2)})  
                
    @api.depends('jul','aug','sep','oct','nov','dec','jan','feb','mar','month')
    def compute_q_2_ytd(self):
        self.q_2_ytd = 0
        aaa = 0
        ss = 0
        tt = 0
        aa = 0
        d = 0
        for app in self:
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
                
            if app.month == 'jul':
                ss = app.jul
                tt = app.t_jul
                aa = app.a_jul
                d = 1
            elif app.month == 'aug':
                ss = app.jul + app.aug
                tt = app.t_jul + app.t_aug
                aa = app.a_jul + app.a_aug
                d = 1+1
            elif app.month == 'sep':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'oct':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'nov':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'dec':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'jan':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'feb':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
            elif app.month == 'mar':
                ss = app.jul + app.aug + app.sep
                tt = app.t_jul + app.t_aug + app.t_sep
                aa = app.a_jul + app.a_aug + app.a_sep
                d = 1+1+1
                
            if ss>0:
                aaa = round((ss/(int(app.weight)*d))*int(app.weight),2)
                app.write({'q_2_ytd': aaa,
                           'q2': aaa})
            if tt >0:
                if app.calculate == 'avg':
                    app.write({'t_q2': round((tt/d),2)})
                else:
                    app.write({'t_q2': round(tt,2)})  
            if aa >0:
                if app.calculate == 'avg':
                    app.write({'a_q2': round((aa/d),2)})
                else:
                    app.write({'a_q2': round(aa,2)})             
    
    @api.depends('oct','nov','dec','jan','feb','mar','month')
    def compute_q_3_ytd(self):
        self.q_3_ytd = 0
        aaa = 0
        ss = 0
        tt = 0
        aa = 0
        d = 0
        for app in self:
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

            if app.month == 'oct':
                ss = app.oct
                tt = app.t_oct
                aa = app.a_oct
                d = 1
            elif app.month == 'nov':
                ss = app.oct + app.nov
                tt = app.t_oct + app.t_nov
                aa = app.a_oct + app.a_nov
                d = 1+1
            elif app.month == 'dec':
                ss = app.oct + app.nov + app.dec
                tt = app.t_oct + app.t_nov + app.t_dec
                aa = app.a_oct + app.a_nov + app.a_dec
                d = 1+1+1
            elif app.month == 'jan':
                ss = app.oct + app.nov + app.dec
                tt = app.t_oct + app.t_nov + app.t_dec
                aa = app.a_oct + app.a_nov + app.a_dec
                d = 1+1+1
            elif app.month == 'feb':
                ss = app.oct + app.nov + app.dec
                tt = app.t_oct + app.t_nov + app.t_dec
                aa = app.a_oct + app.a_nov + app.a_dec
                d = 1+1+1
            elif app.month == 'mar':
                ss = app.oct + app.nov + app.dec
                tt = app.t_oct + app.t_nov + app.t_dec
                aa = app.a_oct + app.a_nov + app.a_dec
                d = 1+1+1
                
            if ss>0:
                aaa = round((ss/(int(app.weight)*d))*int(app.weight),2)
                app.write({'q_3_ytd': aaa,
                           'q3': aaa})
            if tt >0:
                if app.calculate == 'avg':
                    app.write({'t_q3': round((tt/d),2)})
                else:
                    app.write({'t_q3': round(tt,2)})  
            if aa >0:
                if app.calculate == 'avg':
                    app.write({'a_q3': round((aa/d),2)})
                else:
                    app.write({'a_q3': round(aa,2)})                 
                
    @api.depends('jan','feb','mar','month')
    def compute_q_4_ytd(self):
        self.q_4_ytd = 0
        aaa = 0
        ss = 0
        tt = 0
        aa = 0
        d = 0
        for app in self:
            if app.jan == "":
                app.jan = 0
            if app.feb == "":
                app.feb = 0
            if app.mar == "":
                app.mar = 0

            if app.month == 'jan':
                ss = app.jan
                tt = app.t_jan
                aa = app.a_jan
                d = 1
            elif app.month == 'feb':
                ss = app.jan + app.feb
                tt = app.t_jan + app.t_feb
                aa = app.a_jan + app.a_feb
                d = 1+1
            elif app.month == 'mar':
                ss = app.jan + app.feb + app.mar
                tt = app.t_jan + app.t_feb + app.t_mar
                aa = app.a_jan + app.a_feb + app.a_mar
                d = 1+1+1
                
            if ss>0:
                aaa = round((ss/(int(app.weight)*d))*int(app.weight),2)
                app.write({'q_4_ytd': aaa,
                           'q4': aaa})
            if tt >0:
                if app.calculate == 'avg':
                    app.write({'t_q4': round((tt/d),2)})
                else:
                    app.write({'t_q4': round(tt,2)})  
            if aa >0:
                if app.calculate == 'avg':
                    app.write({'a_q4': round((aa/d),2)})
                else:
                    app.write({'a_q4': round(aa,2)})    


    @api.depends('a_apr','a_may','a_jun','a_q1','a_jul','a_aug','a_sep','a_q2','a_oct','a_nov','a_dec','a_q3','a_jan',
                                     'a_feb','a_mar','a_q4','a_ytd','t_apr','t_may','t_jun','t_q1','t_jul','t_aug','t_sep','t_q2','t_oct','t_nov','t_dec','t_q3','t_jan','t_feb','t_mar','t_q4','y_ytd','weight','target','condition','month')  
    def compute_kpi_achv(self):
        for app in self:
            return {}
            if app.condition == 'less':
                if app.a_apr != 0 and app.t_apr != 0 :
                    ka = (t_apr / a_apr)*100
                    app.write({'apr_k': round(ka)})
                else:
                    ka = 0
                    app.write({'apr_k': round(ka)})
                
                if app.a_may != 0 and app.t_may != 0 :
                    ka = (t_may / a_may)*100
                    app.write({'may_k': round(ka)})
                    
                else:
                    ka = 0
                    app.write({'may_k': round(ka)})
                    
                if app.a_jun != 0 and app.t_jun != 0 :
                    ka = (t_jun / a_jun)*100
                    app.write({'jun_k': round(ka)})
                    
                else:
                    ka = 0
                    app.write({'jun_k': round(ka)})
                    
                if app.a_q1 != 0 and app.t_q1 != 0:
                    ka = (t_q1 / a_q1)*100
                    app.write({'q1_k': round(ka)})
                else:
                    ka = 0
                    app.write({'q1_k': round(ka)})
                    
                if app.a_jul != 0 and app.t_jul !=0:
                    ka = (t_jul / a_jul)*100
                    app.write({'jul_k': round(ka)})
                else:
                    ka = 0
                    app.write({'jul_k': round(ka)})
                    
                if app.a_aug != 0 and app.t_aug !=0:
                    ka = (t_aug / a_aug)*100
                    app.write({'aug_k': round(ka)})
                    
                else:
                    ka = 0
                    app.write({'aug_k': round(ka)})
                
                if app.a_sep != 0 and app.t_sep !=0:
                    ka = (t_sep / a_sep)*100
                    app.write({'sep_k': round(ka)})
                    
                else:
                    ka = 0
                    app.write({'sep_k': round(ka)})
                
                if app.a_q2 != 0 and app.t_q2 !=0:
                    ka = (t_q2 / a_q2)*100
                    app.write({'q2_k': round(ka)})
                    
                else:
                    ka = 0
                    app.write({'q2_k': round(ka)})
					
				
					
			# 	if app.a_oct != 0 and app.t_oct !=0:
			# 		ka = (t_oct / a_oct)*100
			# 		app.write({'oct_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'oct_k': round(ka)})
					
			# 	if app.a_nov != 0 and app.t_nov !=0:
			# 		ka = (t_nov / a_nov)*100
			# 		app.write({'nov_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'nov_k': round(ka)})
					
			# 	if app.a_dec != 0 and app.t_dec !=0:
			# 		ka = (t_dec / a_dec)*100
			# 		app.write({'dec_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'dec_k': round(ka)})
					
					
			# 	if app.a_q3 != 0 and app.t_q3 !=0:
			# 		ka = (t_q3 / a_q3)*100
			# 		app.write({'q3_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q3_k': round(ka)})
					
					
			# 	if app.a_jan != 0 and app.t_jan !=0:
			# 		ka = (t_jan / a_jan)*100
			# 		app.write({'jan_k': round(ka)a})
			# 	else:
			# 		ka = 0
			# 		app.write({'jan_k': round(ka)})
					
			# 	if app.a_feb != 0 and app.t_feb !=0:
			# 		ka = (t_feb / a_feb)*100
			# 		app.write({'feb_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'feb_k': round(ka)})
					
			# 	if app.a_mar != 0 and app.t_mar !=0:
			# 		ka = (t_mar / a_mar)*100
			# 		app.write({'mar_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'mar_k': round(ka)})
					
					
			# 	if app.a_q4 != 0 and app.t_q4 !=0:
			# 		ka = (t_q4 / a_q4)*100
			# 		app.write({'q4_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q4_k': round(ka)})
					
					
			# 	if app.a_ytd != 0 and app.t_ytd !=0:
			# 		ka = (t_ytd / a_ytd)*100
			# 		app.write({'ytd_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'ytd_k': round(ka)})
					
				
					
			# else:
			# 	if app.a_apr != 0 and app.t_apr !=0:
			# 		ka = ( a_apr / t_apr)*100
			# 		app.write({'apr_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'apr_k': round(ka)})
					
			# 	if app.a_may != 0 and app.t_may !=0:
			# 		ka = (a_may / t_may)*100
			# 		app.write({'may_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'may_k': round(ka)})
					
			# 	if app.a_jun != 0 and app.t_jun !=0:
			# 		ka = (a_jun / t_jun)*100
			# 		app.write({'jun_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'jun_k': round(ka)})
					
					
			# 	if app.a_q1 != 0 and app.t_q1 !=0:
			# 		ka = (a_q1 / t_q1)*100
			# 		app.write({'q1_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q1_k': round(ka)})
					
				
			# 	if app.a_jul != 0 and app.t_jul !=0:
			# 		ka = (a_jul / t_jul)*100
			# 		app.write({'jul_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'jul_k': round(ka)})
					
			# 	if app.a_aug != 0 and app.t_aug !=0:
			# 		ka = (a_aug / t_aug)*100
			# 		app.write({'aug_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'aug_k': round(ka)})
					
			# 	if app.a_sep != 0 and app.t_sep !=0:
			# 		ka = (a_sep / t_sep)*100
			# 		app.write({'sep_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'sep_k': round(ka)})
					
					
			# 	if app.a_q2 != 0 and app.t_q2 !=0:
			# 		ka = (a_q2 / t_q2)*100
			# 		app.write({'q2_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q2_k': round(ka)})
					
				
					
			# 	if app.a_oct != 0 and app.t_oct !=0:
			# 		ka = (a_oct / t_oct)*100
			# 		app.write({'oct_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'oct_k': round(ka)})
					
			# 	if app.a_nov != 0 and app.t_nov !=0:
			# 		ka = (a_nov / t_nov)*100
			# 		app.write({'nov_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'nov_k': round(ka)})
					
			# 	if app.a_dec != 0 and app.t_dec !=0:
			# 		ka = (a_dec / t_dec)*100
			# 		app.write({'dec_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'dec_k': round(ka)})
					
					
			# 	if app.a_q3 != 0 and app.t_q3 !=0:
			# 		ka = (a_q3 / t_q3)*100
			# 		app.write({'q3_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q3_k': round(ka)})
					
					
			# 	if app.a_jan != 0 and app.t_jan !=0:
			# 		ka = (a_jan / t_jan)*100
			# 		app.write({'jan_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'jan_k': round(ka)})
					
			# 	if app.a_feb != 0 and app.t_feb !=0:
			# 		ka = (a_feb / t_feb)*100
			# 		app.write({'feb_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'feb_k': round(ka)})
					
			# 	if app.a_mar != 0 and app.t_mar !=0:
			# 		ka = (a_mar / t_mar)*100
			# 		app.write({'mar_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'mar_k': round(ka)})
					
					
			# 	if app.a_q4 != 0 and app.t_q4 !=0:
			# 		ka = (a_q4 / t_q4)*100
			# 		app.write({'q4_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'q4_k': round(ka)})
					
					
			# 	if app.a_ytd != 0 and app.t_ytd !=0:
			# 		ka = (a_ytd / t_ytd)*100
			# 		app.write({'ytd_k': round(ka)})
			# 	else:
			# 		ka = 0
			# 		app.write({'ytd_k': round(ka)})
					
