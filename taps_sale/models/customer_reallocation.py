import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class ReAllocation(models.Model):

    _name = 'customer.reallocation'
    _description = 'Customer Reallocation'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    reallocation_line = fields.One2many('customer.reallocation.line', 'reallocation_id', string='Reallocation Line', copy=True)
    # type = fields.Selection([
    #     ('customer', 'Customer'),
    #     ('buyer', 'Buyer')
        
    # ],string="Type", required=True)
    date = fields.Date(string="Date", default=date.today())
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string="Status",  default='draft', tracking=True)
    explanation = fields.Char(string="Explanation", required=True)

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
        user = self.env['crm.approval.matrix'].search([('model_name', '=','customer.reallocation')],limit=1)
        # raise UserError((user.first_approval.id))
        self.activity_schedule('taps_crm.mail_activity_customer_reallocation_first_approval', user_id=user.first_approval.id)
        
    def action_hod(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','customer.reallocation')],limit=1)
        if user.first_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_customer_reallocation_first_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            self.write({'state':'to approve'})
            self.activity_schedule('taps_crm.mail_activity_customer_reallocation_final_approval', user_id=user.second_approval.id)
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))
        
    def action_approve(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','customer.reallocation')],limit=1)
        if user.second_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_customer_reallocation_final_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            data = self.reallocation_line
            for record in data:
                # raise UserError((record.new_user.customers))
                record.new_user.write({'customers': [(4, select_customer)for select_customer in record.select_customer.ids]})
                if record.keep_both:
                    record.existing_user.write({'customers': [(3, select_customer)for select_customer in record.select_customer.ids]})
                self.write({'state':'approved'})
            
           
        else:
            raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))
        
    def action_set_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'cancel'})
    
        

        # Determine the domain based on the selected category
        # if self.type == 'customer':
        #     self.reallocation_line.domain = [('customer_rank', '=', 1)]
        # elif self.type == 'buyer':
        #     self.reallocation_line.domain = [('buyer_rank', '=', 1)]
    
        #     # Set the domain for the 'item' field
        # return {'domain': {'reallocation_line.select_customer': self.reallocation_line.domain}}
       

    


class ReAllocationLine(models.Model):

    _name = 'customer.reallocation.line'
    _description = 'Re-Alcustomerlocation Line'

    
        
    reallocation_id = fields.Many2one('customer.reallocation', string='Reallocation', index=True, required=True, ondelete='cascade')
    name = fields.Char(string="Description")
    # domain = fields.Char()
    
    customer_domain = fields.Char(compute="_compute_customer",readonly=True, store=True)
    buyer_domain = fields.Char(compute="_compute_buyer",readonly=True, store=True)

    select_customer = fields.Many2one('res.partner', string='Allocate Customers', store=True, required=True)
    existing_user = fields.Many2one('customer.allocated', string="Existing Salesperson",)
    new_user = fields.Many2one('customer.allocated', string="New Salesperson",)
    buyer = fields.Many2one('res.partner',string="Buyer") 
    
    keep_both = fields.Boolean('Keep In Both', help="Select to Keep the customer for both salesperson", default=False)
    

    
    @api.onchange('existing_user')
    def _on_change_salesperson(self):
        self.buyer = False
        self.select_customer = False

    @api.depends('buyer')
    def _compute_customer(self):
       
       
       for rec in self:
           if self.existing_user.salesperson:
               
               customer = self.env['customer.allocated.line'].search([('allocated_id', '=', self.existing_user.ids),('buyer', '=', self.buyer.ids)])
               self.customer_domain = json.dumps([('id', 'in', customer.customer.ids)])
           else:
               self.customer_domain = json.dumps([('id', '=', False)])
           # raise UserError((self.customer_domain)) 

    @api.depends('existing_user')
    def _compute_buyer(self):
        for rec in self:
            if self.existing_user.salesperson:
               buyer = self.env['customer.allocated.line'].search([('allocated_id', '=', self.existing_user.ids)])
               self.buyer_domain = json.dumps([('id', 'in', buyer.buyer.ids)])
            else:
                self.buyer_domain = json.dumps([('id', '=', False)])
               
            
    
