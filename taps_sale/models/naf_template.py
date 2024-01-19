import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class NewAccountForm(models.Model):
    _name = 'naf.template'
    _description = 'New Account Form'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name ASC, id DESC"
    _rec_name="name"


    type = fields.Selection([
        ('buyer', 'Buyer'),
        ('customer', 'Customer'),
    ],string="Type", required=True, default='customer')

    name = fields.Char(index=True, string="Name", required=True)
    brand = fields.Many2one('res.partner', domain="[['brand_rank', '=', 1]]", string="Brand")
    group = fields.Many2one('res.partner', string="Group", domain="[['customer_group_rank', '=', 1]]")
    salesperson = fields.Many2one('res.users', domain="[['share', '=', False]]")
    sourcing_type = fields.Selection([
        ('agent', 'AGENT'),
        ('direct', 'DIRECT'),
        ('importer', 'IMPORTER'),
        ('licence', 'LICENCE'),
        ('lo', 'LO'),
    ], string="Sourcing Type")
    sourcing_office = fields.Char(string="Sourcing Office")
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    contact_person = fields.Char(string= "Contact Name")
    email = fields.Char()
    email_formatted = fields.Char(
        'Formatted Email', compute='_compute_email_formatted',
        help='Format email address "Name <email@domain>"')
    phone = fields.Char()
    mobile = fields.Char()
    company_id = fields.Many2one('res.company', 'Company', index=True)
    website = fields.Char('Website Link')
    delivery_address = fields.Text(string="Delivery Address")
    billing_address = fields.Text(string="Billing Address")
    swift_code = fields.Char(string="Swift Code", index=True, help="The Swift Code Number.")
    bond_license = fields.Char(string="Bond License", index=True, help="The Bond License Number.")
    incoterms = fields.Many2one('account.incoterms', string="Incoterms")
    property_payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms")
    property_product_pricelist = fields.Many2one('product.pricelist', string="Pricelist")
    # property_delivery_carrier_id = fields.Many2one('delivery.carrier', string="Delivery Method")
    related_buyer = fields.Many2many('res.partner', relation='customer_related_buyer',column1='partner_id',column2='buyer_id',string="Related Buyer", domain="[['buyer_rank', '=', 1]]")
    
    customer_type = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C'),
    ], string="Customer Type",  default='C')
    customer_status = fields.Selection([
        ('REGULAR', 'REGULAR'),
        ('NON REGULAR', 'NON REGULAR'),
        ('NEW', 'NEW'),
    ], string="Customer Status",  default='NEW')
    

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
    ], string="Status",  default='draft', tracking=True)

    approved_by = fields.Many2one(
        string="Approved By",
        comodel_name="res.users",
    )



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
        self.write({'state':'to approve'})

    def action_approve(self):
        self.write({'state':'cancel'})

    def action_set_draft(self):
        self.write({'state':'draft'})

    def action_cancel(self):
        self.write({'state':'cancel'})

    
    
    
    

