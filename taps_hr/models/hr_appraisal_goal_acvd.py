# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAppraisalGoalsAcvd(models.Model):
    _name = 'hr.appraisal.goal.acvd'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Employee Appraisal Goals Achievement'

    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, tracking=True, default='Goals Monthly Achievement')
    employee_id = fields.Many2one('hr.employee', string="Owner",
         required=True, tracking=True)#default=lambda self: self.env.user.employee_id,
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
        ('mar', 'March'),], string="Month",tracking=True, store=True, required=True)
    acvd_line = fields.One2many('hr.appraisal.goal.acvd.line', 'acvd_id', string='Achievement Lines',tracking=True, store=True, required=True)
    state = fields.Selection([
    ('draft', 'To Submit'),
    ('submit', 'Submitted'),
    ('approved', 'Approved'),
    ('refused', 'Refused')], string='Status', copy=False, 
        index=True, readonly=True, store=True, default='draft', tracking=True, help="Status of the Goals ACVD")
    
    @api.onchange('month')
    def calculate_target_acvd(self):
        for acvd in self.filtered('acvd_line'):
            if self.month == 'apr':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_apr
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_apr
            elif self.month == 'may':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_may
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_may
            elif self.month == 'jun':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_jun
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_jun
            elif self.month == 'jul':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_jul
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_jul
            elif self.month == 'aug':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_aug
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_aug
            elif self.month == 'sep':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_sep
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_sep
            elif self.month == 'oct':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_oct
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_oct
            elif self.month == 'nov':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_nov
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_nov
            elif self.month == 'dec':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_dec
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_dec
            elif self.month == 'jan':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_jan
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_jan
            elif self.month == 'feb':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_feb
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_feb
            elif self.month == 'mar':
                acvd.acvd_line.target = acvd.acvd_line.objective_line_id.t_mar
                acvd.acvd_line.acvd = acvd.acvd_line.objective_line_id.a_mar    

    def button_approve(self, force=False):
        if self.increment_line:
            for app in self.increment_line:
                elist = self.env['hr.employee'].search([('id','=',app.employee_id.id)])
                conlist = self.env['hr.contract'].search([('employee_id','=',app.employee_id.id)])
                # if app.new_job_id:
                #     elist[-1].write({'job_id': app.new_job_id.id})
                #     conlist[-1].write({'job_id': app.new_job_id.id})
                # if app.new_grade:
                #     conlist[-1].write({'structure_type_id': app.new_grade.id})
                # if app.increment_amount > 0:
                #     conlist[-1].write({'wage': app.employee_id.contract_id.wage + app.increment_amount})
                # if app.ot_type == "true":
                #     elist[-1].write({'isovertime': True})
                # if app.ot_type == "false":
                #     elist[-1].write({'isovertime': False})
                # if not app.new_category == app.category:
                #     conlist[-1].write({'category': app.new_category})
                
                    
                    
                    
                    
        self.write({'state': 'approved'})
        return {}

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'submit']:
                continue
            order.write({'state': 'submit'})
        return True     
    
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}    
    
    def button_cancel(self):
        self.write({'state': 'refused'})        
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'GA') == 'GA':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.appraisal.goal.acvd.code')
        return super(HrAppraisalGoalsAcvd, self).create(vals)

class HrAppraisalGoalsAcvdLine(models.Model):
    _name = 'hr.appraisal.goal.acvd.line'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']    
    _description = 'Employee Appraisal Goals Achievement Lines'
    
    acvd_id = fields.Many2one('hr.appraisal.goal.acvd', string='Achievement Reference', index=True, required=True, ondelete='cascade')
    employe_id = fields.Many2one('hr.employee', string='Employee', related='acvd_id.employee_id', store=True, readonly=True)
    objective_line_id = fields.Many2one('hr.appraisal.goal', string='Objective', store=True, index=True, tracking=True,required=True, ondelete='cascade', domain="[('employee_id', '=', employe_id)]")
    target = fields.Float(string="Target", store=True, copy=True,tracking=True, index=True)
    acvd = fields.Float(string="ACVD", store=True, copy=True, tracking=True,index=True)
    acvd_entry = fields.Float(string="ACVD Entry", store=True, copy=True, index=True, tracking=True,required=True)
    
    @api.onchange('objective_line_id')
    def cal_target_acvd(self):
        for line in self.filtered('objective_line_id'):
            if self.acvd_id.month == 'apr':
                line.target = line.objective_line_id.t_apr
                line.acvd = line.objective_line_id.a_apr
            elif self.acvd_id.month == 'may':
                line.target = line.objective_line_id.t_may
                line.acvd = line.objective_line_id.a_may
            elif self.acvd_id.month == 'jun':
                line.target = line.objective_line_id.t_jun
                line.acvd = line.objective_line_id.a_jun
            elif self.acvd_id.month == 'jul':
                line.target = line.objective_line_id.t_jul
                line.acvd = line.objective_line_id.a_jul
            elif self.acvd_id.month == 'aug':
                line.target = line.objective_line_id.t_aug
                line.acvd = line.objective_line_id.a_aug
            elif self.acvd_id.month == 'sep':
                line.target = line.objective_line_id.t_sep
                line.acvd = line.objective_line_id.a_sep
            elif self.acvd_id.month == 'oct':
                line.target = line.objective_line_id.t_oct
                line.acvd = line.objective_line_id.a_oct
            elif self.acvd_id.month == 'nov':
                line.target = line.objective_line_id.t_nov
                line.acvd = line.objective_line_id.a_nov
            elif self.acvd_id.month == 'dec':
                line.target = line.objective_line_id.t_dec
                line.acvd = line.objective_line_id.a_dec
            elif self.acvd_id.month == 'jan':
                line.target = line.objective_line_id.t_jan
                line.acvd = line.objective_line_id.a_jan
            elif self.acvd_id.month == 'feb':
                line.target = line.objective_line_id.t_feb
                line.acvd = line.objective_line_id.a_feb
            elif self.acvd_id.month == 'mar':
                line.target = line.objective_line_id.t_mar
                line.acvd = line.objective_line_id.a_mar  