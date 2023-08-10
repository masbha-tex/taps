# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _, http
from odoo.exceptions import AccessError, UserError, ValidationError
# from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class HrAppraisalGoalsAcvd(models.Model):
    _name = 'hr.appraisal.goal.acvd'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Employee Appraisal Goals Achievement'

    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, tracking=True, default='Goals Monthly Achievement')
    employee_id = fields.Many2one('hr.employee', string="Owner", default=lambda self: self.env.user.employee_id, required=True, tracking=True)
    year = fields.Selection('_get_year_list', 'Year', default=lambda self: self._get_default_year(), tracking=True, store=True, required=True)
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
    acvd_line = fields.One2many('hr.appraisal.goal.acvd.line', 'acvd_id', state={'refused': [('readonly', True)], 'approved': [('readonly', True)]}, string='Achievement Lines', tracking=True, store=True, required=True)
    state = fields.Selection([
    ('draft', 'To Submit'),
    ('submit', 'Submitted'),
    ('approved', 'Approved'),
    ('refused', 'Refused')], string='Status', copy=False, 
        index=True, readonly=True, store=True, default='draft', tracking=True, help="Status of the Goals ACVD")

    @staticmethod
    def _get_year_list():
        current_year = datetime.date.today().year
        year_options = []
        
        for year in range(current_year - 1, current_year + 2):
            year_str = str(year)
            next_year = str(year+1)
            year_label = f'{year_str}-{next_year[2:]}'
            year_options.append((year_str, year_label))
        return year_options     

    @staticmethod
    def _get_default_year():
        current_year = datetime.date.today().year
        return str(current_year)  
        
    @api.onchange('employee_id','year')
    def on_employee_change(self):
        # Clear existing acvd_line records
        self.acvd_line = [(5, 0, 0)]
        if self.employee_id:
            # Fetch the desired acvd_line records based on the selected employee
            deadlines = str(self.year + '-03-31')
            
            acvd_lines = self.env['hr.appraisal.goal'].search([('employee_id','=',self.employee_id.id), ('deadline', '=', deadlines)])
            
            # raise UserError((deadlines))
            # Add the acvd_line records to the one2many field
            # self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': 0, 'acvd': 0}) for id in acvd_lines]
            if self.month == 'apr':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_apr, 'acvd': id.t_apr}) for id in acvd_lines]
            elif self.month == 'may':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_may, 'acvd': id.t_may}) for id in acvd_lines]
            elif self.month == 'jun':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_jun, 'acvd': id.t_jun}) for id in acvd_lines]
            elif self.month == 'jul':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_jul, 'acvd': id.t_jul}) for id in acvd_lines]
            elif self.month == 'aug':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_aug, 'acvd': id.t_aug}) for id in acvd_lines]
            elif self.month == 'sep':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_sep, 'acvd': id.t_sep}) for id in acvd_lines]
            elif self.month == 'oct':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_oct, 'acvd': id.t_oct}) for id in acvd_lines]
            elif self.month == 'nov':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_nov, 'acvd': id.t_nov}) for id in acvd_lines]
            elif self.month == 'dec':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_dec, 'acvd': id.t_dec}) for id in acvd_lines]
            elif self.month == 'jan':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_jan, 'acvd': id.t_jan}) for id in acvd_lines]
            elif self.month == 'feb':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_feb, 'acvd': id.t_feb}) for id in acvd_lines]
            elif self.month == 'mar':
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': id.t_mar, 'acvd': id.t_mar}) for id in acvd_lines]
            else:
                self.acvd_line = [(0, 0, {'objective_line_id': id, 'target': 0, 'acvd': 0}) for id in acvd_lines]
            
            
    @api.onchange('acvd_line')
    def check_duplicate_lines(self):
        for index, line in enumerate(self.acvd_line):
            if not line.id:  # check if row has no id (not yet saved)
                objective_line_id = line.objective_line_id
                for i in range(index + 1, len(self.acvd_line)):
                    if not self.acvd_line[i].id and self.acvd_line[i].objective_line_id.id == objective_line_id.id:
                        raise ValidationError("Duplicate Objective line found: {}".format(objective_line_id.name))
   
               
    @api.onchange('month')
    def calculate_target_acvd_on(self):
        for acvd in self.acvd_line:
            if self.month == 'apr':
                acvd.target = acvd.objective_line_id.t_apr
                acvd.acvd = acvd.objective_line_id.a_apr
            elif self.month == 'may':
                acvd.target = acvd.objective_line_id.t_may
                acvd.acvd = acvd.objective_line_id.a_may
            elif self.month == 'jun':
                acvd.target = acvd.objective_line_id.t_jun
                acvd.acvd = acvd.objective_line_id.a_jun
            elif self.month == 'jul':
                acvd.target = acvd.objective_line_id.t_jul
                acvd.acvd = acvd.objective_line_id.a_jul
            elif self.month == 'aug':
                acvd.target = acvd.objective_line_id.t_aug
                acvd.acvd = acvd.objective_line_id.a_aug
            elif self.month == 'sep':
                acvd.target = acvd.objective_line_id.t_sep
                acvd.acvd = acvd.objective_line_id.a_sep
            elif self.month == 'oct':
                acvd.target = acvd.objective_line_id.t_oct
                acvd.acvd = acvd.objective_line_id.a_oct
            elif self.month == 'nov':
                acvd.target = acvd.objective_line_id.t_nov
                acvd.acvd = acvd.objective_line_id.a_nov
            elif self.month == 'dec':
                acvd.target = acvd.objective_line_id.t_dec
                acvd.acvd = acvd.objective_line_id.a_dec
            elif self.month == 'jan':
                acvd.target = acvd.objective_line_id.t_jan
                acvd.acvd = acvd.objective_line_id.a_jan
            elif self.month == 'feb':
                acvd.target = acvd.objective_line_id.t_feb
                acvd.acvd = acvd.objective_line_id.a_feb
            elif self.month == 'mar':
                acvd.target = acvd.objective_line_id.t_mar
                acvd.acvd = acvd.objective_line_id.a_mar    

    def button_approve(self, force=False):
        for record in self:
            record.write({'state': 'approved'})
            activity_id = self.env['mail.activity'].search([('res_id', '=', self.id), ('user_id', '=', self.env.user.id),
                                                            ('activity_type_id', '=', self.env.ref('taps_lms.mail_act_goals_approval').id)])
            activity_id.action_feedback(feedback='Approved')
        
            deadlines = str(self.year + '-03-31')
            goal = self.env['hr.appraisal.goal'].search([('employee_id','=',self.employee_id.id),('deadline', '=', deadlines)])
            for line in self.acvd_line:
                objec = goal.filtered(lambda g: g.id == line.objective_line_id.id)
                if self.month == 'apr':
                    objec.write({'a_apr':line.acvd_entry})
                elif self.month == 'may':
                    objec.write({'a_may':line.acvd_entry})
                elif self.month == 'jun':
                    objec.write({'a_jun':line.acvd_entry})
                elif self.month == 'jul':
                    objec.write({'a_jul':line.acvd_entry})
                elif self.month == 'aug':
                    objec.write({'a_aug':line.acvd_entry})
                elif self.month == 'sep':
                    objec.write({'a_sep':line.acvd_entry})
                elif self.month == 'oct':
                    objec.write({'a_oct':line.acvd_entry})
                elif self.month == 'nov':
                    objec.write({'a_nov':line.acvd_entry})
                elif self.month == 'dec':
                    objec.write({'a_dec':line.acvd_entry})
                elif self.month == 'jan':
                    objec.write({'a_jan':line.acvd_entry})
                elif self.month == 'feb':
                    objec.write({'a_feb':line.acvd_entry})
                elif self.month == 'mar':
                    objec.write({'a_mar':line.acvd_entry})
            
        return {
                'effect': {
                    'fadeout': 'slow',
                    'message': 'Appraisal Goals Achievement Approved',
                    'type': 'rainbow_man',
                    'img_url': 'taps_hr/static/img/success.png'
                }
            }
            
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'submit']:
                continue
            order.write({'state': 'submit'})
            users = self.employee_id.parent_id.user_id.id
            self.activity_schedule('taps_lms.mail_act_goals_approval', user_id=users, note=f'Please Approve Goals Achievement for the Month of {self.month, self.year} and Code is {self.name}')
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
    _description = 'Employee Appraisal Goals Achievement Lines'
    _order = 'acvd_id, sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    acvd_id = fields.Many2one('hr.appraisal.goal.acvd', string='Achievement Reference', index=True, required=True, ondelete='cascade')
    employe_id = fields.Many2one('hr.employee', string='Employee', related='acvd_id.employee_id', store=True, readonly=True)
    objective_line_id = fields.Many2one('hr.appraisal.goal', string='Objective', store=True, index=True, tracking=True,required=True, ondelete='cascade', domain="[('employee_id', '=', employe_id)]")
    selected = fields.Boolean(string="Selected", store=True, default=False)
    target = fields.Float(string="Target", store=True, copy=True,tracking=True, index=True)
    acvd = fields.Float(string="ACVD", store=True, copy=True, tracking=True,index=True)
    acvd_entry = fields.Float(string="ACVD Entry", store=True, copy=True, index=True, tracking=True,required=True)
    

    def write(self, values):
        if 'objective_line_id' in values:
            for line in self:
                # if line.acvd_id.state != 'draft':
                line.acvd_id.message_post_with_view('taps_hr.track_acvd_line_objective_template',
                                                     values={'line': line, 'objective_line_id': values['objective_line_id']},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'target' in values:
            for line in self:
                # if line.acvd_id.state != 'draft':
                line.acvd_id.message_post_with_view('taps_hr.track_acvd_line_target_template',
                                                     values={'line': line, 'target': values['target']},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'acvd' in values:
            for line in self:
                # if line.acvd_id.state != 'draft':
                line.acvd_id.message_post_with_view('taps_hr.track_acvd_line_acvd_template',
                                                     values={'line': line, 'acvd': values['acvd']},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        if 'acvd_entry' in values:
            for line in self:
                # if line.acvd_id.state != 'draft':
                line.acvd_id.message_post_with_view('taps_hr.track_acvd_line_entry_template',
                                                     values={'line': line, 'acvd_entry': values['acvd_entry']},
                                                     subtype_id=self.env.ref('mail.mt_note').id)
        return super(HrAppraisalGoalsAcvdLine, self).write(values)

    def unlink(self):
        for line in self:
            if line.acvd_id.state in ['submit', 'approved']:
                raise UserError(_('Cannot delete a Objective line which is in state \'%s\'.') % (line.acvd_id.state,))
        return super(HrAppraisalGoalsAcvdLine, self).unlink()    
    
    @api.onchange('objective_line_id')
    def compute_target_acvd(self):
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
                