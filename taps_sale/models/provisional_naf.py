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
            user = self.env['sale.approval.matrix'].search([('model_name', '=','provisional.template.customer')],limit=1)    
        result = super(ProvisionalNaf, self).create(vals)
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
        return {}

    def action_approve(self):
        user = self.env['sale.approval.matrix'].search([('model_name','=','provisional.template.customer')],limit=1)
        
        if user.second_approval.id == self.env.user.id:
            result = self._check_duplicate_partner(self.type)
            raise UserError((result))
                    
        # else:
        #     raise UserError(("Only "+ user.second_approval.partner_id.name + " can approve this"))
        return {}

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

    def open_similar_customers_popup(self):
        return {}
    
