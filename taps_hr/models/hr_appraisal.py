# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"
    _description = "Employee Appraisal"
    _order = 'employee_id'


    ytd_weightage_acvd = fields.Float(string='YTD Weightage ACVD', copy=True,  compute='_compute_ytd_weightage_acvd', default="0")
    total_weightage = fields.Float(string='Weightage', copy=True, default="0", compute='_compute_ytd_weightage_acvd')
    manager_ids = fields.Many2many('hr.employee', 'appraisal_manager_rel', 'hr_appraisal_id', domain=[])
    q_1_ytd = fields.Float(string="Q1",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_2_ytd = fields.Float(string="Q2",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_3_ytd = fields.Float(string="Q3",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_4_ytd = fields.Float(string="Q4",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    kpi_state = fields.Char(string="Kpi Status",store=True)
    
    
    # @api.multi
    def action_create_meeting_event(self):
        view_id = self.env.ref('taps_hr.view_meeting_event_wizard_form').id
        return {
            'name': 'Create Meeting Event',
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'meeting.event.wizard',
            'views': [(view_id, 'form')],
            'target': 'new',
            # 'context': {'default_meeting_date': self.date_close},  # Pass the meeting_date to the wizard
        }    

    def _compute_ytd_weightage_acvd(self):
        for appraisal in self:
            app_goal = self.env['hr.appraisal.goal'].search([('employee_id', '=', appraisal.employee_id.id), ('deadline', '=', appraisal.date_close)])
            # ytd = 0
            # weight = 0
            # ytd = sum(app_goal.mapped('y_ytd'))
            # weight = sum(app_goal.mapped('weight'))
            appraisal.ytd_weightage_acvd = sum(app_goal.mapped('y_ytd'))
            appraisal.total_weightage = sum(app_goal.mapped('weight'))
            appraisal.q_1_ytd = sum(app_goal.mapped('q_1_ytd'))
            appraisal.q_2_ytd = sum(app_goal.mapped('q_2_ytd'))
            appraisal.q_3_ytd = sum(app_goal.mapped('q_3_ytd'))
            appraisal.q_4_ytd = sum(app_goal.mapped('q_4_ytd'))

    def action_open_goals(self):
        self.ensure_one()
        return {
            'name': _('%s Goals') % self.employee_id.name,
            'view_mode': 'kanban,tree,form',
            'res_model': 'hr.appraisal.goal',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': [('employee_id', '=', self.employee_id.id), ('deadline', '=', self.date_close)],
            'context': {'default_employee_id': self.employee_id.id},
        }
    def action_done(self):
        current_date = datetime.date.today()
        self.activity_feedback(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
        self.write({'state': 'done'})
        for appraisal in self:
            appraisal.employee_id.write({
                'last_appraisal_id': appraisal.id,
                'last_appraisal_date': appraisal.date_close,#current_date
                'next_appraisal_date': False})
    @api.model
    def create(self, vals):
        result = super(HrAppraisal, self).create(vals)
        if vals.get('state') and vals['state'] == 'pending':
            self.send_appraisal()

        result.employee_id.sudo().write({
            'next_appraisal_date': result.date_final_interview,
        })
        result.subscribe_employees()
        return result
        
    def write(self, vals):
        self._check_access(vals.keys())
        if 'state' in vals and vals['state'] == 'pending':
            self.send_appraisal()
        result = super(HrAppraisal, self).write(vals)
        if vals.get('date_final_interview'):
            self.mapped('employee_id').write({'next_appraisal_date': vals.get('date_final_interview')})
            self.activity_reschedule(['mail.mail_activity_data_meeting'], date_deadline=vals['date_final_interview'])
        return result
            
class MeetingEventWizard(models.TransientModel):
    _name = 'meeting.event.wizard'
    _description = 'Meeting Event Wizard'

    meeting_date = fields.Datetime(string='Meeting Date', required=True)
    meeting_subject = fields.Char(string='Subject', default="Appraisal Meeting")
    reminder = fields.Many2many('calendar.alarm',string='Reminders')
    location = fields.Char(string='Location')
    duration = fields.Float(string='Duration')
    note = fields.Html()
    # Add more fields if needed for your wizard

    def create_event_and_appraisal(self):
        active_ids = self._context.get('active_ids', [])
        if not active_ids:
            return

        meeting_date = self.meeting_date + relativedelta(hours=self.duration)  # Assuming you have a field 'meeting_date' in the wizard

        # Call the action_create_meeting_event method for each hr.appraisal record
        hr_appraisal = self.env['hr.appraisal'].browse(active_ids)
        user_id = self.env.user.id
        partner_id = [appraisal.employee_id.address_home_id.id for appraisal in hr_appraisal]
        user_partner_ids = self.env.user.partner_id.id 
        combined_ids = partner_id + [user_partner_ids]
        
        # raise UserError((combined_ids))
        hr_appraisal.mapped('meeting_id').unlink()
        event_vals = {
            'name': self.meeting_subject,
            'start': self.meeting_date,
            'stop': meeting_date,
            'start_date': self.meeting_date,
            'stop_date': meeting_date,
            'alarm_ids': self.reminder,
            'duration': self.duration,
            'location': self.location,
            'description': self.note,
            'user_id': user_id,
            'partner_ids': [(6, 0, combined_ids)], 
        }
        meeting = self.env['calendar.event'].create(event_vals)
        # self.activity_unlink(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
        # raise UserError((self.employee_id))
        for appraisal in hr_appraisal:
            appraisal.meeting_id = meeting.id
            appraisal.date_final_interview = self.meeting_date
            # meeting_activity_type = self.env['mail.activity.type'].search([('category', '=', 'meeting')], limit=1)
            appraisal.activity_unlink(['mail.mail_activity_data_meeting', 'mail.mail_activity_data_todo'])
    
            # Create an activity note for each partner in partner_ids
        # for appraisal in hr_appraisal:
            employee = appraisal.employee_id
            managers = appraisal.manager_ids
            if employee.user_id:
                appraisal.activity_schedule(
                    'mail.mail_activity_data_meeting', 
                    self.meeting_date,
                    summary=_(self.meeting_subject),
                    note=_(self.note),
                    user_id=employee.user_id.id)
            for manager in managers.filtered(lambda m: m.user_id):
                appraisal.activity_schedule(
                    'mail.mail_activity_data_meeting', 
                    self.meeting_date,
                    summary=_(self.meeting_subject),
                    note=_(self.note),
                    user_id=manager.user_id.id)
        
        return {'type': 'ir.actions.act_window_close'}
        
