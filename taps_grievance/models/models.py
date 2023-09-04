# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HrGrievance(models.Model):
    _name = 'hr.grievance'
    _description = 'Employee Grievance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    
    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New'))
    employee_id = fields.Many2one('hr.employee', "Employee", required=True)
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)    
    type = fields.Selection([
            ('0', 'Telephone'),
            ('1', 'Other Verbal'),
            ('2', 'In writing')], "Type of Misconduct", help="This is the type by which the complaint was received.")
    details = fields.Html('Details of Misconduct')
    action_taken = fields.Selection([
        ('1', 'Verbal Warning'),
        ('2', 'Advise'),
        ('3', 'Formal Warning'),
        ('4', 'Show Cause'),
        ('5', 'Show Cause of Suspension'),
        ('6', 'Dismissal'),
        ('7', 'Termination')], 'Action to be taken', tracking=True)    
    
    submit_by = fields.Many2one('hr.employee',"Complaint By",required=True)
    state = fields.Selection([
            ('draft', 'New'),
            ('pending', 'Pending'),
            ('closed', 'Closed')], 'Status', required=True, tracking=True, default='draft')
    complaint_date = fields.Date('Complaint date', required=True, default=fields.Date.today())
    responsible_id = fields.Many2one('res.users', ondelete='set null', string="Responsible", index=True, tracking=True)

    def action_submit(self):
        self.state = 'pending'
        # users = self.env.ref('taps_lms.group_manager_lms').users
        # for user in users:
        #     self.activity_schedule('taps_lms.mail_act_course_approval', user_id=user.id, note=f'Please Approve Training course {self.name}')
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            complaint_date = vals.get('complaint_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.grievance', sequence_date=complaint_date)
        return super(HrGrievance, self).create(vals)