import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class NewAccountForm(models.Model):
    _name = 'naf.template'
    _description = 'New Account Form'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name ASC, id DESC"
    _rec_name="name"


    assign_line = fields.One2many('assign.user.line', 'naf_id', string='Assign Line', copy=True)
    
    type = fields.Selection([
        ('customer', 'Customer'),
        ('buyinghouse', 'Buying House'),
        ('buyer', 'Buyer'),
        
    ],string="Type", required=True)

    name = fields.Char(index=True, string="Name", required=True)
    code = fields.Char(index=True, string="Code")
    pnaf = fields.Many2one('provisional.template', string="P-NAF")
    pnaf_code = fields.Char(related='pnaf.code' , string="P-Naf Code")
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
        ('hod', 'HOD'),
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
    related_customer = fields.Many2many('res.partner', relation='partner_related_customer_naf',column1='partner',column2='customer',string="Related Customer", domain="[['customer_rank', '=',1]]")
    buyer_group = fields.Many2one('res.partner', string="Buyer Group", domain="[('brand_rank', '=', 1)]")
    sourcing_office = fields.Many2many('buyer.sourcing.office', string="Sourcing Office")


    @api.model
    def create(self, vals):
        
        if vals.get('code', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['code'] = self.env['ir.sequence'].next_by_code('naf.template', sequence_date=seq_date) or _('New')
        a = self._check_duplicate_partner(vals)
        if a == 1:
            raise UserError(("This "+vals['type'] + "already exist in Database"))
        else:
            result = super(NewAccountForm, self).create(vals)
            return result
    
    @api.depends('name', 'email')
    def _compute_email_formatted(self):
        """ Compute formatted email for partner, using formataddr. Be defensive
        in computation, notably

          * double format: if email already holds a formatted email like
            'Name' <email@domain.com> we should not use it as it to compute
            email formatted like "Name <'Name' <email@domain.com>>";
          * multi emails: sometimes this field is used to hold several addresses
            like email1@domain.com, email2@domain.com. We currently let this value
            untouched, but remove any formatting from multi emails;
          * invalid email: if something is wrong, keep it in email_formatted as
            this eases management and understanding of failures at mail.mail,
            mail.notification and mailing.trace level;
          * void email: email_formatted is False, as we cannot do anything with
            it;
        """
        self.email_formatted = False
        for partner in self:
            emails_normalized = tools.email_normalize_all(partner.email)
            if emails_normalized:
                # note: multi-email input leads to invalid email like "Name" <email1, email2>
                # but this is current behavior in Odoo 14+ and some servers allow it
                partner.email_formatted = tools.formataddr((
                    partner.name or u"False",
                    ','.join(emails_normalized)
                ))
            elif partner.email:
                partner.email_formatted = tools.formataddr((
                    partner.name or u"False",
                    partner.email
                ))
                
    def action_submit_approval(self):
        if self.type == 'buyer':
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.buyer')],limit=1)
        else:
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.customer')],limit=1)
            
        result = self._check_duplicate_partner()
        if result == 1:
            raise UserError(("This "+self.type + "already exist in Database"))
        else:
            self.env['mail.activity'].sudo().create({
                    'activity_type_id': self.env.ref('taps_sale.mail_activity_naf_first_approval').id,
                    'res_id': self.id,
                    'res_model_id': self.env.ref('taps_sale.model_naf_template').id,
                    'user_id': user.first_approval.id
            })
            self.write({'state':'inter'})

    
        
        activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_approve').id)])
        activity_id.action_feedback(feedback="Approved")
        other_activity_ids = self.env['mail.activity'].search([('res_id','=', self.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_approve').id)])
        
        other_activity_ids.unlink()

    def action_set_draft(self):
        self.write({'state':'draft'})
        
    def action_teamleader(self):
        if self.type == 'buyer':
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.buyer')],limit=1)
            
        else:
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.customer')],limit=1)
            
          
        if user.first_approval.id == self.env.user.id:
            result = self._check_duplicate_partner()
            if result == 1:
                raise UserError(("This "+self.type + "already exist in Database"))
            else:
                if (self.type == 'customer' and self.assign_line) or (self.type == 'buyer' and self.assign_line) or (self.type == 'buyinghouse'):
                    activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_first_approval').id)])
                    activity_id.action_feedback(feedback="Approved")
                    other_activity_ids = self.env['mail.activity'].search([('res_id','=', self.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_first_approval').id)])
                    if other_activity_ids:
                        other_activity_ids.unlink()
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('taps_sale.mail_activity_naf_second_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env.ref('taps_sale.model_naf_template').id,
                        'user_id': user.second_approval.id
                    })
                    template_id = self.env.ref('taps_sale.naf_assign_naf_hod_email_template')

                    if template_id:
                        template_id.write({
                            'email_to': user.second_approval.partner_id.email,
                            'email_from': 'odoo@texzipperbd.com',
                            'email_cc' : 'asraful.haque@texzipperbd.com',
                        })
                        ctx ={'name': user.second_approval.partner_id.name}
                        template_id.with_context(ctx).send_mail(self.id, force_send=True)
                    self.write({'state':'hod'})
                else:
                    raise UserError(("Kindly Assign Salesperson Or Marketing Person"))
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))

    def action_hod(self):
        if self.type == 'buyer':
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.buyer')],limit=1)
        else:
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.customer')],limit=1)
        if user.second_approval.id == self.env.user.id:
            result = self._check_duplicate_partner()
            if result == 1:
                raise UserError(("This "+self.type + "already exist in Database"))
            else:
                if (self.type == 'customer' and self.assign_line) or (self.type == 'buyer' and self.assign_line) or (self.type == 'buyinghouse'):
                    activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_second_approval').id)])
                    activity_id.action_feedback(feedback="Approved")
                    self.write({'state':'to approve'})
                    # self.activity_schedule('taps_sale.mail_activity_naf_final_approval', user_id=user.third_approval.id)
                    self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('taps_sale.mail_activity_naf_final_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env.ref('taps_sale.model_naf_template').id,
                        'user_id': user.third_approval.id
                    })
                    template_id = self.env.ref('taps_sale.naf_assign_naf_ceo_email_template')

                    if template_id:
                        template_id.write({
                            'email_to': user.third_approval.partner_id.email,
                            'email_from': 'odoo@texzipperbd.com',
                            'email_cc' : 'asraful.haque@texzipperbd.com',
                        })
                        ctx ={'name': user.third_approval.partner_id.name}
                        template_id.with_context(ctx).send_mail(self.id, force_send=True)
                else:
                    raise UserError(("Kindly Assign Salesperson Or Marketing Person"))
        else:
            raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))


    def action_approve(self):
        if self.type == 'buyer':
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.buyer')],limit=1)
        else:
            user = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.customer')],limit=1)
        
        if user.third_approval.id == self.env.user.id:
            result = self._check_duplicate_partner()
            if result == 1:
                raise UserError(("This "+self.type + "already exist in Database"))
            else:
                
                
                
                customer_rank = 0
                buying_house_rank = 0
                buyer_rank = 0
                if self. type == 'customer':
                    customer_rank=1
                if self. type == 'buyinghouse':
                    buying_house_rank=1
                if self. type == 'buyer':
                    buyer_rank=1
                data = {
                        'name': self.name,
                        'group': self.customer_group.id,
                        'brand' : self.buyer_group.id,
                        'sourcing_office': self.sourcing_office,
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
                        'buyer_rank' : buyer_rank,
                        'buying_house_rank' : buying_house_rank,
                        'incoterms': self.incoterms.id,
                        'company_type': 'company',
                        'property_product_pricelist': 1,
                        }
                new_customer = self.env['res.partner'].sudo().create(data)
                self.env.cr.commit()
                # raise UserError((new_customer))
                self.write({'state': 'approved'})
                activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_final_approval').id)])
                activity_id.action_feedback(feedback="Approved")
                if self. type == 'customer':
                    buyers = self.env['res.partner'].search([('id', 'in', self.buyer.ids)])
                    buyers.write({'related_customer': [(4, customer)for customer in new_customer.ids]})
                    if self.buying_house:
                        self.buying_house.write({'related_customer': [(4, customer)for customer in new_customer.ids]})
                if self. type == 'buyinghouse' or self.type == 'buyer':
                    # raise UserError((self.related_customer))
                    customers = self.env['res.partner'].search([('id', 'in', self.related_customer.ids)])
                    new_customer.write({'related_customer': [(4, customer)for customer in customers.ids]})
                if self.assign_line:
                    for rec in self.assign_line:
                        if self.type == 'customer':
                            data = {'buyer': rec.buyer.id,
                                    'customer': new_customer.id,
                                    'allocated_id': rec.salesperson.id,
                                   }
                            new_allocation = self.env['customer.allocated.line'].sudo().create(data)
                        if self.type == 'buyer':
                            # raise UserError((rec.marketing_person.id))
                            data_1 = {'buyer': new_customer.id,
                                    'allocated_id': rec.marketing_person.id,
                                   }
                            new_allocation_1 = self.env['buyer.allocated.line'].sudo().create(data_1)
                            
                
                
                
        else:
            raise UserError(("Only "+ user.third_approval.partner_id.name + " can approve this"))

    # def action_cancel(self):
    #     self.write({'state':'cancel'})

    def _check_duplicate_partner(self, vals=None):
        
        list = ['limited','ltd','co','mpany', '.',',',' ','(',')', 'pvt', 'private','apparels','apparel']
        duplicate = 0
        duplicate_name = ''
        if vals:
            if vals['type'] == 'customer':
                exists = self.env['res.partner'].search([('customer_rank', '=', 1)])
            if vals['type'] == 'buyinghouse':
                exists = self.env['res.partner'].search([('buying_house_rank', '=', 1)])
            if vals['type'] == 'buyer':
                exists = self.env['res.partner'].search([('buyer_rank', '=', 1)])
        else:
            if self.type == 'customer':
                exists = self.env['res.partner'].search([('customer_rank', '=', 1)])
            if self.type == 'buyinghouse':
                exists = self.env['res.partner'].search([('buying_house_rank', '=', 1)])
            if self.type == 'buyer':
                exists = self.env['res.partner'].search([('buyer_rank', '=', 1)])
        
        # raise UserError((vals['name']))
        if vals:
            output_string = vals['name'].lower()
        else:
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


    def _update_activity(self, id):
        naf = self.env['naf.template'].search([('id', '=', id)])
        if naf.state == 'inter':
            if (naf.type == 'customer') or (naf.type == 'buyinghouse'):
                app_mat = naf.env['sale.approval.matrix'].sudo().search([('model_name', '=','naf.template.customer')], limit=1)
                # raise UserError((app_mat.id))
                template_id = naf.env.ref('taps_sale.naf_assign_core_leader_customer_email_template')
                email_to = 'abdur.rahman@texzipperbd.com'
            elif naf.type == 'buyer':
                app_mat = naf.env['sale.approval.matrix'].sudo().search([('model_name', '=','naf.template.buyer')],limit=1)
                template_id = naf.env.ref('taps_sale.naf_assign_naf_core_leader_buyer_email_template')
                email_to = 'abdur.rahman@texzipperbd.com'
            # raise UserError((app_mat.id))
            naf.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('taps_sale.mail_activity_naf_first_approval').id,
                        'res_id': naf.id,
                        'res_model_id': naf.env.ref('taps_sale.model_naf_template').id,
                        'user_id': app_mat.first_approval.id,
                        
                        })
            # if template_id:
            #     template_id.write({
            #             'email_to': email_to,
            #             'email_from': 'odoo@texzipperbd.com',
            #             'email_cc' : 'asraful.haque@texzipperbd.com',
            #         })
                    
            #     template_id.send_mail(id, force_send=False)
                
            
            
       

class AssignUserLine(models.Model):
    _name = 'assign.user.line'
    _description = 'Assign User Line'
    
    # _order = "name ASC, id DESC"
    # _rec_name="name"
    name = fields.Char(string="Description")
    naf_id = fields.Many2one('naf.template', string='NAF ID', index=True, required=True, ondelete='cascade')
    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]")
    salesperson = fields.Many2one('customer.allocated', string="Salesperson")
    marketing_person = fields.Many2one('buyer.allocated', string="Marketing Person")
    type_naf = fields.Selection(related="naf_id.type")
    
    

