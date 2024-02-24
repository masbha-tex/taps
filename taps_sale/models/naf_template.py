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
    related_customer = fields.Many2many('res.partner', relation='partner_related_customer_naf',column1='partner',column2='customer',string="Related Customer", domain="[['customer_rank', '=',1]]")
    buyer_group = fields.Many2one('res.partner', string="Buyer Group", domain="[('brand_rank', '=', 1)]")
    sourcing_office = fields.Many2many('buyer.sourcing.office', string="Sourcing Office")



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
        users = self.env.ref('sales_team.group_sale_manager').users
        for user in users:
            # activity_type=self.env.ref()
            self.activity_schedule('taps_sale.mail_activity_naf_approve', user_id=user.id)
        
        self.write({'state':'inter'})

    def action_approve(self):
        self.write({'state':'cancel'})
        
        activity_id = self.env['mail.activity'].search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_approve').id)])
        activity_id.action_feedback(feedback="Approved")
        other_activity_ids = self.env['mail.activity'].search([('res_id','=', self.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_naf_approve').id)])
        
        other_activity_ids.unlink()

    def action_set_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'cancel'})




class AssignUserLine(models.Model):
    _name = 'assign.user.line'
    _description = 'Assign User Line'
    
    # _order = "name ASC, id DESC"
    # _rec_name="name"
    name = fields.Char(string="Description")
    naf_id = fields.Many2one('naf.template', string='NAF ID', index=True, required=True, ondelete='cascade')
    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]")
    salesperson = fields.Many2one('customer.allocated', string="Salesperson")
    marketing_person = fields.Many2one('res.partner', string="Marketing Person")
    type_naf = fields.Selection(related="naf_id.type")
    
    

