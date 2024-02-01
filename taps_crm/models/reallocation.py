import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class ReAllocation(models.Model):

    _name = 'reallocation.template'
    _description = 'Re-Allocation Form'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    reallocation_line = fields.One2many('reallocation.template.line', 'reallocation_id', string='Reallocation Line', copy=True)
    type = fields.Selection([
        ('customer', 'Customer'),
        ('buyer', 'Buyer')
        
    ],string="Type", required=True)
    date = fields.Date(string="Date", default=date.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string="Status",  default='draft', tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('reallocation.template', sequence_date=seq_date) or _('New')
        
        result = super(ReAllocation, self).create(vals)
        return result

    def action_submit_approval(self):
        self.write({'state':'submitted'})
    def action_hod(self):
        self.write({'state':'to approve'})
    def action_approve(self):
        self.write({'state':'approved'})
    def action_set_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'cancel'})
    @api.onchange('type')
    def _on_change_type(self):
        self.reallocation_line = False
        

        # Determine the domain based on the selected category
        # if self.type == 'customer':
        #     self.reallocation_line.domain = [('customer_rank', '=', 1)]
        # elif self.type == 'buyer':
        #     self.reallocation_line.domain = [('buyer_rank', '=', 1)]
    
        #     # Set the domain for the 'item' field
        # return {'domain': {'reallocation_line.select_customer': self.reallocation_line.domain}}
       

    


class ReAllocationLine(models.Model):

    _name = 'reallocation.template.line'
    _description = 'Re-Allocation Line'

    
        
    reallocation_id = fields.Many2one('reallocation.template', string='Reallocation', index=True, required=True, ondelete='cascade')
    name = fields.Char(string="Explanation", required=True)
    # domain = fields.Char()
    select_customer = fields.Many2one('res.partner', string='Select Customer', domain="[('customer_rank', '=', 1)]")
    existing_user = fields.Many2many('res.users', string="Sales/Marketing person", domain="[('share', '=', False)]", readonly=True)
    new_user = fields.Many2one('res.users', string=" Assigned Sales/Marketing person", domain="[('share', '=', False)]")
    
    is_removed = fields.Boolean('Select to remove the customer from previous person',default=False)

    
    @api.onchange('select_customer')
    def _compute_salesperson(self):
        
        assigned_user = self.env['customer.allocation'].search([('customers', 'in', self.select_customer.id)])
        if assigned_user:
            self.existing_user = assigned_user.salesperson
        else:
            self.existing_user = False


    
        
            
    
