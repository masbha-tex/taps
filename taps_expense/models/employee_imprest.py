import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class HrImprest(models.Model):
    _name = "hr.imprest"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']        
    _description = "HR Imprest"
    _check_company_auto = True

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.imprest.name')
        return super(HrImprest, self).create(vals)     
    
    #active = fields.Boolean('Active', compute='_compute_can_reset')
    name = fields.Char('Imprest Reference', required=True, readonly=True, index=True, copy=False, default='New')
    description = fields.Char('Description', required=True, store=True, copy=True)
    
    imprest_amount_bdt = fields.Float("Amount ৳", store=True, copy=True, digits='Product Unit of Measure')
    imprest_amount_usd = fields.Float("Amount $", store=True, copy=True, digits='Product Unit of Measure')
    imprest_company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    #, default=lambda self: self.env.company
    imprest_currency = fields.Many2one('res.currency', string='Currency', required=True)
    imprest_date = fields.Date(default=fields.Date.context_today, string="Imprest Date")
    imprest_employee = fields.Many2one('hr.employee', string="Employee", store=True, readonly=False, tracking=True)
    #check_company=True
    imprest_notes = fields.Text('Notes...')
    imprest_work_mail = fields.Char('Work Mail',related='imprest_employee.work_email', readonly=True)
    imprest_work_phone =  fields.Char('Work Phone',related='imprest_employee.mobile_phone', readonly=True)
    state = fields.Selection([
        ('draft', 'To Submit'),
        ('submit', 'Submitted'),
        ('checked', 'Checked'),
        ('approved', 'Approved'),
        ('refused', 'Refused')
    ], string='Status', copy=False, index=True, readonly=True, store=True, default='draft', help="Status of the imprest.", tracking=True)
    
    #["|",["x_studio_currency","=","USD"],["x_studio_currency","=",False]]
    #["|",["imprest_currency","=","USD"],["imprest_currency","=",False]

    def button_approve(self, force=False):
        #self = self.filtered(lambda order: order._approval_allowed())
        self.write({'state': 'approved'})
        return {}
    
    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'submit']:
                continue
            order.write({'state': 'submit'})
        return True        
    
    def button_check(self):
        for order in self:
            if order.state not in ['draft', 'submit', 'checked']:
                continue
            order.write({'state': 'checked'})
        return True 
    
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}    
    
    def button_cancel(self):
        self.write({'state': 'refused'})    
        
    def action_get_attachment_view(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'hr.imprest'), ('res_id', 'in', self.ids)]
        res['context'] = {'default_res_model': 'hr.imprest', 'default_res_id': self.id}
        return res