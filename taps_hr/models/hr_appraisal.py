# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
import logging

from dateutil.relativedelta import relativedelta
from odoo import tools
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import matplotlib.pyplot as plt
from io import BytesIO
import base64
import numpy as np

_logger = logging.getLogger(__name__)


class HrAppraisal(models.Model):
    _inherit = "hr.appraisal"
    _order = 'employee_id'


    ytd_weightage_acvd = fields.Float(string='YTD Weightage ACVD', copy=True,  compute='_compute_ytd_weightage_acvd', default="0")
    total_weightage = fields.Float(string='Weightage', copy=True, default="0", compute='_compute_ytd_weightage_acvd')
    manager_ids = fields.Many2many('hr.employee', 'appraisal_manager_rel', 'hr_appraisal_id', domain=[])
    q_1_ytd = fields.Float(string="Q1",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_2_ytd = fields.Float(string="Q2",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_3_ytd = fields.Float(string="Q3",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    q_4_ytd = fields.Float(string="Q4",copy=True, compute='_compute_ytd_weightage_acvd', default="0")
    kpi_state = fields.Char(string="Kpi Status",store=True)
    employee_group = fields.Many2one('hr.employee.group', store=True, related = 'employee_id.employee_group', string="Group", related_sudo=False, help="What would be the group of this employee?")
    category = fields.Selection(store=True, related = 'employee_id.contract_id.category', string="Category", related_sudo=False, help='Category of the Employee')
    chart_image = fields.Binary(string="Pie Chart Image", compute='_generate_chart_image', copy=True)    
    
  

    # def _generate_chart_image(self):
    #     for record in self:
    #         data = [('Q 1', record.q_1_ytd if record.q_1_ytd else 0), ('Q 2', record.q_2_ytd if record.q_2_ytd else 0), ('Q 3', record.q_3_ytd if record.q_3_ytd else 0), ('Q 4', record.q_4_ytd if record.q_4_ytd else 0)] # Replace 'kpi_data' with the actual field containing your data
    #         chart_image = self.generate_pie_chart(data)
    #         # record.chart_image = base64.b64encode(chart_image.getvalue()).decode('utf-8')
    #         record.chart_image = base64.b64encode(chart_image.getvalue())
    #         # raise UserError((record.chart_image))


    def _generate_chart_image(self):
        # if self.ytd_k <= 30:
        q1 = q2 = q3 = q4 = 0    
        for record in self:
            app_goal = self.env['hr.appraisal.goal'].search([('employee_id', '=', record.employee_id.id), ('deadline', '=', record.date_close), ('description', '!=', 'Strategic Projects'), ('description', '!=', False)])
            # mapp = app_goal.mapped('description')
            # raise UserError((mapp))
            f_1 = app_goal.filtered(lambda x: x.ytd_k <= 30)
            if f_1:
                q1 = len(f_1)
            f_2 = app_goal.filtered(lambda x: x.ytd_k > 30 and x.ytd_k <= 69)
            if f_2:
                q2 = len(f_2)
            f_3 = app_goal.filtered(lambda x: x.ytd_k > 69 and x.ytd_k <= 99)
            if f_3:
                q3 = len(f_3)
            f_4 = app_goal.filtered(lambda x: x.ytd_k > 99)
            if f_4:
                q4 = len(f_4)

            

                
            data = [('More then 100', q4), ('30 to 69', q2), ('70 to 99', q3), ('Less Then 30', q1)] # Replace 'kpi_data' with the actual field containing your data
            chart_image = self.generate_pie_chart(data)
            # record.chart_image = base64.b64encode(chart_image.getvalue()).decode('utf-8')
            record.chart_image = base64.b64encode(chart_image.getvalue())
            # raise UserError((record.chart_image))

    def generate_pie_chart(self, data):
        # Assuming data is a tuple, modify this according to your actual data structure
        labels = [item[0] for item in data]
        values = [item[1] for item in data]

        # raise UserError((labels,values))
        # values = [0 if np.isnan(val) else val for val in values]
        
        def my_autopct(pct):
            total = sum(values)
            # val = round((pct * total / 100.0),2)
            val = round((pct * total / 100.0))
            return f'{val}'

        plt.pie(values, labels=labels, autopct=my_autopct, startangle=90, wedgeprops=dict(width=0.5), textprops={'fontsize': 15}, pctdistance=0.7)
        # plt.gca().set_title('KPI Score', fontsize=20)
        plt.suptitle('KPI Score', fontsize=15, y=0.5, color='#BDBDBD')
        
        plt.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.

        # Save the plot to a BytesIO buffer
        buffer = BytesIO()
        plt.savefig(buffer, format='png')
        plt.close()
        buffer.seek(0)

        return buffer
        
  
  
    
    
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
            # appraisal._generate_chart_image()

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
        
