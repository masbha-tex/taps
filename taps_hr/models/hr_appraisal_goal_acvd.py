# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

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
    acvd_line = fields.One2many('hr.appraisal.goal.acvd.line', 'acvd_id', state={'refused': [('readonly', True)], 'approved': [('readonly', True)]}, string='Achievement Lines',tracking=True, store=True, required=True)
    state = fields.Selection([
    ('draft', 'To Submit'),
    ('submit', 'Submitted'),
    ('approved', 'Approved'),
    ('refused', 'Refused')], string='Status', copy=False, 
        index=True, readonly=True, store=True, default='draft', tracking=True, help="Status of the Goals ACVD")
    
    # @api.onchange('acvd_line')
    # def check_duplicates(self):
    #     for line in self.acvd_line:
    #         if line.id:
    #             continue  # skip lines that are already saved
    #         for other in self.acvd_line.filtered(lambda x: x != line):
    #             if other.objective_line_id == line.objective_line_id:
    #                 raise ValidationError("Duplicate objective found: {}".format(line.objective_line_id.name))
    @api.onchange('acvd_line')
    def check_duplicate_lines(self):
        for index, line in enumerate(self.acvd_line):
            if not line.id:  # check if row has no id (not yet saved)
                objective_line_id = line.objective_line_id
                for i in range(index + 1, len(self.acvd_line)):
                    if not self.acvd_line[i].id and self.acvd_line[i].objective_line_id.id == objective_line_id.id:
                        raise ValidationError("Duplicate Objective line found: {}".format(objective_line_id.name))
   
               
    # @api.onchange('month')
    # def calculate_target_acvd(self):
    #     for acvd in self.acvd_line:
    #         if self.month == 'apr':
    #             acvd.target = acvd.objective_line_id.t_apr
    #             acvd.acvd = acvd.objective_line_id.a_apr
    #         elif self.month == 'may':
    #             acvd.target = acvd.objective_line_id.t_may
    #             acvd.acvd = acvd.objective_line_id.a_may
    #         elif self.month == 'jun':
    #             acvd.target = acvd.objective_line_id.t_jun
    #             acvd.acvd = acvd.objective_line_id.a_jun
    #         elif self.month == 'jul':
    #             acvd.target = acvd.objective_line_id.t_jul
    #             acvd.acvd = acvd.objective_line_id.a_jul
    #         elif self.month == 'aug':
    #             acvd.target = acvd.objective_line_id.t_aug
    #             acvd.acvd = acvd.objective_line_id.a_aug
    #         elif self.month == 'sep':
    #             acvd.target = acvd.objective_line_id.t_sep
    #             acvd.acvd = acvd.objective_line_id.a_sep
    #         elif self.month == 'oct':
    #             acvd.target = acvd.objective_line_id.t_oct
    #             acvd.acvd = acvd.objective_line_id.a_oct
    #         elif self.month == 'nov':
    #             acvd.target = acvd.objective_line_id.t_nov
    #             acvd.acvd = acvd.objective_line_id.a_nov
    #         elif self.month == 'dec':
    #             acvd.target = acvd.objective_line_id.t_dec
    #             acvd.acvd = acvd.objective_line_id.a_dec
    #         elif self.month == 'jan':
    #             acvd.target = acvd.objective_line_id.t_jan
    #             acvd.acvd = acvd.objective_line_id.a_jan
    #         elif self.month == 'feb':
    #             acvd.target = acvd.objective_line_id.t_feb
    #             acvd.acvd = acvd.objective_line_id.a_feb
    #         elif self.month == 'mar':
    #             acvd.target = acvd.objective_line_id.t_mar
    #             acvd.acvd = acvd.objective_line_id.a_mar    

    def button_approve(self, force=False):
        self.write({'state': 'approved'})
        goal = self.env['hr.appraisal.goal'].search([('employee_id','=',self.employee_id.id)])
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
        
        return {}
        # if self.increment_line:
        #     for app in self.increment_line:
        #         elist = self.env['hr.employee'].search([('id','=',app.employee_id.id)])
        #         conlist = self.env['hr.contract'].search([('employee_id','=',app.employee_id.id)])
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
    _description = 'Employee Appraisal Goals Achievement Lines'
    _order = 'acvd_id, sequence, id'
    
    sequence = fields.Integer(string='Sequence', default=10)
    acvd_id = fields.Many2one('hr.appraisal.goal.acvd', string='Achievement Reference', index=True, required=True, ondelete='cascade')
    employe_id = fields.Many2one('hr.employee', string='Employee', related='acvd_id.employee_id', store=True, readonly=True)
    objective_line_id = fields.Many2one('hr.appraisal.goal', string='Objective', store=True, index=True, tracking=True,required=True, ondelete='cascade', domain="[('employee_id', '=', employe_id)]")
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
                