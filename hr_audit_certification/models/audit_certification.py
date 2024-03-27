# -*- coding: utf-8 -*-

from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError

class HrAuditCertification(models.Model):
    _name = 'hr.audit.certification'
    _description = 'Audit Certification'
    _inherit = ['mail.thread', 'mail.activity.mixin']  

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    active = fields.Boolean('Active', default=True)
    # employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)    
    # company_id = fields.Many2one(related='employee_id.company_id', store=True)
    # department_id = fields.Many2one(related='employee_id.department_id', store=True)
    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    date = fields.Date(string = "Date")
    audit_certification = fields.Text('Audit Certification', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('In Progress', 'In Progress'),
        ('Pending', 'Pending'),
        ('Critical Pending', 'Critical Pending'),
        ('Done', 'Done'),
        ('Cancel', 'Cancel')], 'Status', required=True, tracking=True, default='draft')
    type = fields.Selection(selection=[
        ('1', 'Fire Safety'),
        ('2', 'Machine Safety'),
        ('3', 'Buidling Safety'),
        ('4', 'Electrical Safety'),
        ('5', 'Chemical Safety'),
        ('6', 'Social Compliance Aspects'),
        ('7', 'OHS'),
        ('8', 'Protection of the Environment')], string="Type", tracking=True)
    severity = fields.Selection(selection=[
        ('1', 'Low'),
        ('2', 'Medium'),
        ('3', 'High')], string="Severity", tracking=True)
    observation = fields.Text('Observation', tracking=True) 
    corrective_action = fields.Text('Corrective Action', tracking=True)
    preventive_action = fields.Text('Preventive Action', tracking=True)
    remarks = fields.Text('Remarks', tracking=True)
    
    def action_inprogress(self):
        if self.state == 'draft':
            self.state = 'In Progress'
            
    def action_pending(self):
        if self.state == 'In Progress':
            self.state = 'Pending' 
                
    def action_c_pending(self):
        if self.state == 'Pending':
            self.state = 'Critical Pending'
                
    def action_done(self):
        if self.state == 'Critical Pending':
            self.state = 'Done'
            
    # def action_cancel(self):
    #     if self.state == 'Done':
    #         self.state = 'Cancel'
            
    def action_draft(self):
        if self.state == 'Done':
            self.state = 'draft' 

            
    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            date = vals.get('date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.audit.certification', sequence_date=date)
        return super(HrAuditCertification, self).create(vals)
