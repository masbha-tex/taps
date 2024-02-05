import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class BrandReAllocation(models.Model):

    _name = 'brand.reallocation'
    _description = 'Brand Reallocation'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string="Name",required=True, copy=False, index=True, readonly=True,  default=lambda self: _('New'))
    reallocation_line = fields.One2many('brand.reallocation.line', 'reallocation_id', string='Reallocation Line', copy=True)
    
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
            vals['name'] = self.env['ir.sequence'].next_by_code('brand.reallocation', sequence_date=seq_date) or _('New')
        
        result = super(BrandReAllocation, self).create(vals)
        return result

    def action_submit_approval(self):
        self.write({'state':'submitted'})
        user = self.env['crm.approval.matrix'].search([('model_name', '=','brand.reallocation')],limit=1)
        # raise UserError((user.first_approval.id))
        self.activity_schedule('taps_crm.mail_activity_brand_reallocation_first_approval', user_id=user.first_approval.id)
        
    def action_hod(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','brand.reallocation')],limit=1)
        if user.first_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_brand_reallocation_first_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            self.write({'state':'to approve'})
            self.activity_schedule('taps_crm.mail_activity_brand_reallocation_final_approval', user_id=user.second_approval.id)
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))
        
    def action_approve(self):
        user = self.env['crm.approval.matrix'].search([('model_name', '=','brand.reallocation')],limit=1)
        if user.second_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_crm.mail_activity_brand_reallocation_final_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            data = self.reallocation_line
            for record in data:
                record.new_user.write({'brand': [(4, select_brand)for select_brand in record.select_brand.ids]})
                if record.keep_both:
                    record.existing_user.write({'brand': [(3, select_brand)for select_brand in record.select_brand.ids]})
                self.write({'state':'approved'})
            
           
        else:
            raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))
        
    def action_set_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'cancel'})
    
        
       

    


class ReAllocationLine(models.Model):

    _name = 'brand.reallocation.line'
    _description = 'Re-allocation Line'

    
        
    reallocation_id = fields.Many2one('brand.reallocation', string='Reallocation', index=True, required=True, ondelete='cascade')
    name = fields.Char(string="Description")
    # domain = fields.Char()
    brand_domain = fields.Char(compute="_compute_brand",readonly=True, store=True)

    select_brand = fields.Many2many('res.partner', string='Allocate Brands', store=True, required=True)
    existing_user = fields.Many2one('brand.allocation', string="Existing Marketing Person",)
    new_user = fields.Many2one('brand.allocation', string="New Marketing Person",)
     
    
    keep_both = fields.Boolean('Keep In Both', help="Select to Keep the brand for both salesperson", default=False)
    

    
    @api.onchange('existing_user')
    def _on_change_salesperson(self):
        self.select_brand = False

    @api.depends('existing_user')
    def _compute_brand(self):
       
       
       for rec in self:
           if self.existing_user.marketing_person:
                  self.brand_domain = json.dumps([('id', 'in', self.existing_user.brand.ids)])
           else:
               self.brand_domain = json.dumps([('id', '=', False)])
           
        
            
    
