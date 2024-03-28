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
        ('buyer', 'Buyer'),
        
    ],string="Type", required=True, default="customer")

    name = fields.Char(index=True, string="Name", required=True)
    code = fields.Char(index=True, string="Code")
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
   
    state = fields.Selection([
        ('draft', 'Draft'),
        ('to approve', 'To Approve'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel'),
        ('listed', 'Listed'),
    ], string="Status",  default='draft', tracking=True)

    approved_by = fields.Many2one(
        string="Approved By",
        comodel_name="res.users",
    )


    @api.model
    def create(self, vals):
        
        if vals.get('code', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            vals['code'] = self.env['ir.sequence'].next_by_code('provisional.template', sequence_date=seq_date) or _('New')
        naf= self._check_duplicate_naf(vals)
        if naf == 1:
            raise UserError(("This "+vals['type'] + "already exist in NAF"))
        else:
            a = self._check_duplicate_partner(vals)
            if a == 1:
                raise UserError(("This "+vals['type'] + "already exist in Database"))
            else:
                result = super(ProvisionalNaf, self).create(vals)
        return result
        
    def action_approval(self):
        
        user = self.env['sale.approval.matrix'].search([('model_name', '=','provisional.template')],limit=1)

        naf= self._check_duplicate_naf()
        if naf == 1:
            raise UserError(("This "+ self.type + " already exist in NAF"))
        else:
            
            result = self._check_duplicate_partner()
            if result == 1:
                raise UserError(("This "+self.type + "already exist in Database"))
            else:
                self.env['mail.activity'].sudo().create({
                        'activity_type_id': self.env.ref('taps_sale.mail_activity_provisional_naf_approval').id,
                        'res_id': self.id,
                        'res_model_id': self.env.ref('taps_sale.model_provisional_template').id,
                        'user_id': user.first_approval.id
                })
                
                template_id = self.env.ref('taps_sale.p_naf_assign_hod_email_template')
                
                if template_id:
                    template_id.write({
                        'email_to': user.first_approval.partner_id.email,
                        'email_from': 'odoo@texzipperbd.com',
                        'email_cc' : 'asraful.haque@texzipperbd.com',
                    })
                    ctx ={'name': user.third_approval.partner_id.name}
                    template_id.with_context(ctx).send_mail(self.id, force_send=True)
                self.write({'state':'to approve'})
        
    

        

    def action_approve(self):
        user = self.env['sale.approval.matrix'].search([('model_name', '=','provisional.template')],limit=1)
        
        if user.first_approval.id == self.env.user.id:
            result = self._check_duplicate_partner()
            if result == 1:
                raise UserError(("This "+self.type + "already exist in Database"))
            else:
                # raise UserError((self.create_uid.partner_id.name))
                data = {
                        'type' : self.type,
                        'name': self.name,
                        'street' : self.street,
                        'street2': self.street2,
                        'city' : self.city,
                        'state_id': self.state_id.id,
                        'country_id' : self.country_id.id,
                        'contact_person': self.contact_person,
                        'phone': self.phone,
                        'mobile' : self.mobile,
                        'email' : self.email,
                        'pnaf' : self.id,
                        'state' : 'draft',
                        'raised_by': self.create_uid.id,
                        }
                new_record = self.env['naf.template'].sudo().create(data)
                # self.env.cr.commit()
                # raise UserError((new_customer))
                
                activity_id = self.env['mail.activity'].sudo().search([('res_id','=', self.id),('user_id','=', self.env.user.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_provisional_naf_approval').id)])
                activity_id.action_feedback(feedback="Approved")
                other_activity_ids = self.env['mail.activity'].search([('res_id','=', self.id),('activity_type_id','=', self.env.ref('taps_sale.mail_activity_provisional_naf_approval').id)])
                if other_activity_ids:
                    other_activity_ids.unlink()
                # if self. type == 'customer' or self. type == 'buyinghouse':
                #     app_mat = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.customer')],limit=1)
                # else:
                #     app_mat = self.env['sale.approval.matrix'].search([('model_name', '=','naf.template.buyer')],limit=1)
                    
                # self.env['mail.activity'].sudo().create({
                #     'activity_type_id': self.env.ref('taps_sale.mail_activity_naf_first_approval').id,
                #     'res_id': new_record.id,
                #     'res_model_id': self.env.ref('taps_sale.model_naf_template').id,
                #     'user_id': app_mat.first_approval.id
                #     })
                template_id = self.env.ref('taps_sale.p_naf_confirm_email_template')
            
                if template_id:
                    template_id.write({
                        'email_to': self.create_uid.partner_id.email,
                        'email_from': 'odoo@texzipperbd.com',
                        'email_cc' : 'asraful.haque@texzipperbd.com',
                    })
                    
                    template_id.send_mail(self.id, force_send=True)
                            
                self.write({'state': 'approved'})
                
                
        else:
            raise UserError(("Only "+ user.first_approval.partner_id.name + " can approve this"))
        
    def _check_duplicate_naf(self, vals=None):
        duplicate = 0
        exists = False
        if vals:
            exists = self.env['naf.template'].sudo().search([('name', '=', vals['name']),('type', '=', vals['type'])])
        else:
            exists = self.env['naf.template'].sudo().search([('name', '=', self.name),('type', '=', self.type)])

        if exists:
            duplicate = 1
            
        return duplicate
            
            

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

        
       
        
    
