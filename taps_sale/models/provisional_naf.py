from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class ProvisionalNaf(models.Model):
    _name = 'provisional.template'
    _description = 'Provisional Naf'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name ASC, id DESC"
    _rec_name="name"


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
    buyer = fields.Many2one('res.partner', string="Buyer", domain="[['buyer_rank' ,'=', 1]]")
    salesperson = fields.Many2one('res.users', domain="[['share', '=', False],['sale_team_id', '!=', False]]",)

    @api.model
    def create(self, vals):
        
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['name'] = self.env['ir.sequence'].next_by_code('provisional.template', sequence_date=seq_date) or _('New')
        if vals.get('state'):
            vals['state'] = 'inter'
            
        result = super(ProvisionalNaf, self).create(vals)
        return result
    
    
