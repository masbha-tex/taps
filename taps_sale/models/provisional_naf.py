from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class ProvisionalNaf(models.Model):
    _name = 'provisional.template'
    _description = 'Provisional Naf'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name ASC, id DESC"
    _rec_name="name"

    assign_line = fields.One2many('assign.user', 'provisional_id', string='Assign Line', copy=True, states={'approved': [('readonly', True)]})
    
    type = fields.Selection([
        ('customer', 'Customer'),
        ('buyinghouse', 'Buying House'),
        
    ],string="Type", required=True)

    name = fields.Char(index=True, string="Name", required=True)
    street = fields.Char(required=True)
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char(required=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', required=True)

    contact_person = fields.Char(string= "Contact Name", required=True)
    email = fields.Char()
    email_formatted = fields.Char(
        'Formatted Email', compute='_compute_email_formatted',
        help='Format email address "Name <email@domain>"')
    phone = fields.Char()
    mobile = fields.Char(required=True)
    company_id = fields.Many2one('res.company', 'Company', index=True)
    website = fields.Char('Website Link')
    delivery_address = fields.Text(string="Delivery Address")
    billing_address = fields.Text(string="Billing Address")
    swift_code = fields.Char(string="Swift Code", index=True, help="The Swift Code Number.")
    bond_license = fields.Char(string="Bond License", index=True, help="The Bond License Number.")
    incoterms = fields.Many2one('account.incoterms', string="Incoterms")
    property_payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('inter', 'Intermediate'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string="Status",  default='draft', tracking=True)

    approved_by = fields.Many2one(
        string="Approved By",
        comodel_name="res.users",
    )
    customer_group = fields.Many2one('res.partner', string="Customer Group", domain="[['customer_group_rank', '=', 1]]")
    buyer = fields.Many2many('res.partner', string="Buyer", domain="[['buyer_rank' ,'=', 1]]")
    buying_house = fields.Many2one('res.partner', string="Buying House", domain="[('buying_house_rank', '=', 1)]")
    custom_delivery_method = fields.Selection([
        ('By Road', 'By Road'),
        ('By Air', 'By Air'),
        ('By Sea', 'By Sea'),
        ('By Air/By Sea', 'By Air/By Sea'),
    ], string="Delivery Method", default='By Road')
    related_customer = fields.Many2many('res.partner', relation='partner_related_customer',column1='partner',column2='customer',string="Related Customer", domain="[['customer_rank', '=',1]]")
    # salesperson = fields.Many2one('res.users', domain="[['share', '=', False],['sale_team_id', '!=', False]]",)

    @api.model
    def create(self, vals):
        
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('provisional.template', sequence_date=seq_date) or _('New')
        
        vals['state'] = 'inter'   
        result = super(ProvisionalNaf, self).create(vals)
        user = self.env['sale.approval.matrix'].search([('model_name', '=','provisional.template.customer')],limit=1) 
        self.env['mail.activity'].sudo().create({
                'activity_type_id': self.env.ref('taps_sale.mail_activity_provisional_naf_first_approval').id,
                'res_id': result.id,
                'res_model_id': self.env.ref('taps_sale.model_provisional_template').id,
                'user_id': user.first_approval.id
        })
        return result


    def action_hod(self):
        user = self.env['sale.approval.matrix'].search([('model_name', '=','provisional.template.customer')],limit=1)
        if user.first_approval.id == self.env.user.id:
            activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_provisional_naf_first_approval').id)])
            activity_id.action_feedback(feedback="Approved")
            self.write({'state':'to approve'})
            self.activity_schedule('taps_sale.mail_activity_provisional_naf_final_approval', user_id=user.second_approval.id)
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))
        

    def action_approve(self):
        user = self.env['sale.approval.matrix'].search([('model_name','=','provisional.template.customer')],limit=1)
        
        if user.second_approval.id == self.env.user.id:
            result = self._check_duplicate_partner(self.type)
            if result == 1:
                raise UserError(("This Customer already exist in Database"))
            else:
                
                
                
                customer_rank = 0
                buying_house_rank = 0
                if self. type == 'customer':
                    customer_rank=1
                if self. type == 'buyinghouse':
                    buying_house_rank=1
                data = {
                        'name': self.name,
                        'group': self.customer_group.id,
                        'related_buyer': self.buyer,
                        # 'user_id' : self.salesperson.id,
                        'street' : self.street,
                        # 'street2': self.strret2,
                        'city' : self.city,
                        'state_id': self.state_id.id,
                        'country_id' : self.country_id.id,
                        'contact_person': self.contact_person,
                        'phone': self.phone,
                        'mobile' : self.mobile,
                        'email' : self.email,
                        'website' : self.website,
                        'swift_code' : self.swift_code,
                        'bond_license': self.bond_license,
                        'property_payment_term_id': self.property_payment_term_id.id,
                        'delivery_address': self.delivery_address,
                        'billing_address': self.billing_address,
                        'customer_rank' : customer_rank,
                        'buying_house_rank' : buying_house_rank,
                        'incoterms': self.incoterms.id,
                        'company_type': 'company',
                        }
                new_customer = self.env['res.partner'].sudo().create(data)
                self.env.cr.commit()
                # raise UserError((new_customer))
                
                activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_provisional_naf_final_approval').id)])
                activity_id.action_feedback(feedback="Approved")
                if self. type == 'customer':
                    buyers = self.env['res.partner'].search([('id', 'in', self.buyer.ids)])
                    buyers.write({'related_customer': [(4, customer)for customer in new_customer.ids]})
                    if self.buying_house:
                        self.buying_house.write({'related_customer': [(4, customer)for customer in new_customer.ids]})
                if self. type == 'buyinghouse':
                    # raise UserError((self.related_customer))
                    customers = self.env['res.partner'].search([('id', 'in', self.related_customer.ids)])
                    new_customer.write({'related_customer': [(4, customer)for customer in customers.ids]})
                if self.assign_line:
                    for rec in self.assign_line:
                        data = {'buyer': rec.buyer.id,
                                'customer': new_customer.id,
                                'allocated_id': rec.salesperson.id,
                               }
                        new_allocation = self.env['customer.allocated.line'].sudo().create(data)
                self.write({'state': 'approved'})
                
                
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))
            

    def _check_duplicate_partner(self, type):
        
        list = ['limited','ltd','co','mpany', '.',',',' ','(',')', 'pvt', 'private','apparels','apparel']
        duplicate = 0
        duplicate_name = ''
        if type == 'customer':
            exists = self.env['res.partner'].search([('customer_rank', '>=', 1)])
        if type == 'buyinghouse':
            exists = self.env['res.partner'].search([('buying_house_rank', '>=', 1)])
        
        # raise UserError((exists))
        output_string = self.name.lower()
        for record in exists:
            check_string = record.name.lower()
            for word in list:
                output_string = output_string.replace(word,'')
                check_string = check_string.replace(word,'')
                if record.name and (check_string == output_string):
                    duplicate_name = record.name
                    duplicate = 1
            
            
        
        return duplicate

        
       
        


class AssignUser(models.Model):
    _name = 'assign.user'
    _description = 'Assign User'
    
    # _order = "name ASC, id DESC"
    # _rec_name="name"
    name = fields.Char(string="Description")
    provisional_id = fields.Many2one('provisional.template', string='Provisional ID', index=True, required=True, ondelete='cascade')
    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]")
    salesperson = fields.Many2one('customer.allocated', string="Salesperson")
    
    
