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
            ('draft', 'Draft'),
            ('Submit', 'Submit'),
            ('Primary Invesigation', 'Primary Invesigation'),
            ('Letter Submit', 'Letter Submit'),
            ('Return Answard', 'Return Answard'),
            ('Satisfactory', 'Satisfactory'),
            ('Closed', 'Closed')], 'Status', required=True, tracking=True, default='draft')
    complaint_date = fields.Date('Complaint date', required=True, default=fields.Date.today())
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    next_user = fields.Many2one('res.users', ondelete='set null', string="Next User", index=True, tracking=True)

    def action_submit(self):
        # self.state = 'pending'
        if self.state == 'draft':
            self.state = 'Submit'
        elif self.state == 'Submit':
            self.state = 'Primary Invesigation'
        elif self.state == 'Primary Invesigation':
            self.state = 'Letter Submit'
        elif self.state == 'Letter Submit':
            self.state = 'Return Answard'
        elif self.state == 'Return Answard':
            self.state = 'Satisfactory'
        elif self.state == 'Satisfactory':
            self.state = 'Closed'

        # self.next_user = self.env['res.users'].search([('login','in',())])            
        # users = self.env.ref('taps_lms.group_manager_lms').users
        # for user in users:
        #     self.activity_schedule('taps_lms.mail_act_course_approval', user_id=user.id, note=f'Please Approve Training course {self.name}')
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            complaint_date = vals.get('complaint_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.grievance', sequence_date=complaint_date)
        return super(HrGrievance, self).create(vals)
        
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for grievance in self:
            grievance.attachment_number = attachment.get(grievance.id, 0)        
        

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.grievance'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'hr.grievance',
            'default_res_id': self.id,
        }
        return res
        
class HrEmployee(models.Model):
	_inherit="hr.employee"
	
	grievance_count = fields.Integer(compute='_compute_grievance_count', store=False, string='Grievance')
	
	def _compute_grievance_count(self):
		Grievance = self.env['hr.grievance']
		self.grievance_count = Grievance.search_count([('employee_id','=',self.id)])
        
# class HrEmployeePublic(models.Model):
#     _inherit = 'hr.employee.public'

#     grievance_count = fields.Integer(readonly=True)