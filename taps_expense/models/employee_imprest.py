import re

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import email_split, float_is_zero

class HrImprest(models.Model):
    _name = "hr.imprest"
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']        
    _description = "HR Imprest"
    _check_company_auto = True
    
    #active = fields.Boolean('Active', compute='_compute_can_reset')
    name = fields.Char('Name', store=True, required=True, copy=True)
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

    
    #["|",["x_studio_currency","=","USD"],["x_studio_currency","=",False]]
    #["|",["imprest_currency","=","USD"],["imprest_currency","=",False]
    