import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError



class BuyerName(models.Model):
    _name = 'sale.buyer'
    _rec_name= 'name'
    _description = 'Buyer List'
    
    name = fields.Char(string='Buyer Name')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    buyer_rank = fields.Integer(default=0, copy=False)
    brand_rank = fields.Integer(default=0, copy=False)
    customer_group_rank = fields.Integer(default=0, copy=False)
    sale_representative = fields.Many2one('sale.representative', string="Sale Representative", )
    related_buyer = fields.Many2many('res.partner', relation='partner_related_buyer_rel',column1='partner_id',column2='buyer_id',string="Related Buyer", compute='_compute_buyer')
    related_customer = fields.Many2many('res.partner', relation='partner_related_customer_rel',column1='partner_id',column2='customer_id',string="Related Customer")
    contact_person = fields.Char(string="Contact Name", help="Contact Person Name")
    contact_mobile = fields.Char(string="Contact Person's Mobile")
    group = fields.Many2one('res.partner', string="Group")
    brand = fields.Many2one('res.partner', string="Brand")
    delivery_address = fields.Text(string="Delivery Address")
    billing_address = fields.Text(string="Billing Address")
    swift_code = fields.Char(string="Swift Code", index=True, help="The Swift Code Number.")
    bond_license = fields.Char(string="Bond License", index=True, help="The Bond License Number.")
    incoterms = fields.Many2one('account.incoterms', string="Incoterms")
    sourcing_office = fields.Char(string="Sourcing Office")
    sourcing_type = fields.Selection([
        ('agent', 'AGENT'),
        ('direct', 'DIRECT'),
        ('importer', 'IMPORTER'),
        ('licence', 'LICENCE'),
        ('lo', 'LO'),
    ], string="Sourcing Type")
    property_account_receivable_id = fields.Many2one(
        'account.account',
        string='Account Receivable',
        help='Default account for receivables',
        default=lambda self: self._get_default_account_receivable_id(),
    )
    property_account_payable_id = fields.Many2one(
        'account.account',
        string="Account Payable",
        help='Default account for receivables',
        default=lambda self: self._get_default_account_payable_id(),
        )
    customer_type = fields.Selection([
        ('A', 'A'),
        ('B', 'B'),
        ('C', 'C')
        
    ], string="Customer Type", default='C')
    custom_delivery_method = fields.Selection([
        ('By Road', 'By Road'),
        ('By Air', 'By Air'),
        ('By Sea', 'By Sea'),
        ('By Air/By Sea', 'By Air/By Sea'),
    ], string="Customer Delivery Method", default='By Road')

    customer_status = fields.Selection([
        ('New', 'New'),
        ('Non-Regular', 'Non-Regular'),
        ('Regular', 'Regular'),
    ], string="Customer Status", default='New')

    # user_id = fields.Many2one(
    #     'res.users', string='Salesperson', index=True, tracking=2, default=lambda self: self.env.user,
    #     domain=lambda self: "[('groups_id', '=', {}), ('share', '=', False), ('company_ids', '=', company_id)]".format(
    #         self.env.ref("sales_team.group_sale_salesman").id
    #     ), compute='_compute_salesperson', inverse='_inverse_salesperson')

    def _compute_buyer(self):
        order = self.env['sale.order'].search([('partner_id.id', '=', self.id)])
        order_sorted = order.mapped('buyer_name')
        # raise UserError((order_sorted))
        if order_sorted:
            self.related_buyer =[(6, 0, order_sorted.ids)]
        else:
            self.related_buyer = False
        

    # def _compute_salesperson(self):
    #     order = self.env['sale.order'].search([('partner_id.id', '=', self.id)], limit=1)
    #     if order:
    #         for rec in order:
    #             self.user_id = rec.user_id
    #     else:
    #         self.user_id= False

    # def _inverse_salesperson(self):
    #     pass
    
    @api.onchange('phone','mobile','name','email','website')
    def _onchange_company_id(self):
        # Automatically update the property_account_payable_id based on the current company
        self.property_account_receivable_id = self._get_default_account_receivable_id()
        self.property_account_payable_id = self._get_default_account_payable_id()
    # def write(self, vals):
    #     # Call the parent write method
    #     result = super(ResPartner, self).write(vals)

    #     # Update property_account_payable_id based on the current company
    #     if 'company_id' not in vals:
    #         # Only update when company_id is not explicitly changed
    #         current_company = self.env.company
    #         property_account_receivable_id = self._get_default_account_receivable_id()
    #         self.property_account_receivable_id = property_account_receivable_id
    #         property_account_payable_id = self._get_default_account_payable_id()
    #         self.property_account_payable_id = property_account_payable_id

    #     return result
        
    def _get_default_account_receivable_id(self):
        
        property_account_receivable_id = self.env['account.account'].search([('internal_type', '=', 'receivable'),('company_id', '=', self.env.company.id)], limit=1)
        # raise UserError((return property_account_receivable_id.id))
        return property_account_receivable_id.id
        
    
    def _get_default_account_payable_id(self):
        
        property_account_payable_id = self.env['account.account'].search([('internal_type', '=', 'payable'),('company_id', '=', self.env.company.id)], limit=1)
        # raise UserError((return property_account_receivable_id.id))
        return property_account_payable_id.id
    
    
    @api.model_create_multi
    def create(self, vals_list):
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        is_supplier = search_partner_mode == 'supplier'
        is_buyer = search_partner_mode == 'buyer'
        is_brand = search_partner_mode == 'brand'
        is_customer_group = search_partner_mode == 'customer_group'
        # raise UserError((vals_list))
        if is_supplier:
            exists = self.env['res.partner'].search([('supplier_rank', '>=', 1)])
        if is_customer:
            exists = self.env['res.partner'].search([('customer_rank', '>=', 1)])
        if is_buyer:
            exists = self.env['res.partner'].search([('buyer_rank', '>=', 1)])
        if is_brand:
            exists = self.env['res.partner'].search([('brand_rank', '>=', 1)])
        if is_customer_group:
            exists = self.env['res.partner'].search([('customer_group_rank', '>=', 1)])
        
            
            
            
        if search_partner_mode:
            list = ['limited','ltd','co','mpany', '.',',',' ','(',')']
            duplicate = 0
            duplicate_name = ''
            for vals in vals_list:
                if is_customer and 'customer_rank' not in vals:
                    output_string = vals['name'].lower()
                    for record in exists:
                        # mapping_table = str.maketrans({'LIMITED':'','.':''})
                        
                        
                        if record.name:
                            check_string = record.name.lower()
                        for word in list:
                             
                            output_string = output_string.replace(word,'')
                            check_string = check_string.replace(word,'')
                            # raise UserError((record.name.lower()))
                            if record.name and (check_string == output_string):
                                duplicate_name = record.name
                                duplicate = 1
                    # raise UserError((duplicate))
                    if duplicate == 1:
                        raise UserError((duplicate_name + " is already exist."))
                    else:
                        vals['customer_rank'] = 1
                elif is_supplier and 'supplier_rank' not in vals:
                    output_string = vals['name'].lower()
                    for record in exists:
                        # mapping_table = str.maketrans({'LIMITED':'','.':''})
                        
                        
                        if record.name:
                            check_string = record.name.lower()
                        for word in list:
                             
                            output_string = output_string.replace(word,'')
                            check_string = check_string.replace(word,'')
                            # raise UserError((record.name.lower()))
                            if record.name and (check_string == output_string):
                                duplicate_name = record.name
                                duplicate = 1
                    # raise UserError((duplicate))
                    if duplicate == 1:
                        raise UserError((duplicate_name + " is already exist."))
                    else:
                        vals['supplier_rank'] = 1
                elif is_buyer and 'buyer_rank' not in vals:
                    output_string = vals['name'].lower()
                    for record in exists:
                        # mapping_table = str.maketrans({'LIMITED':'','.':''})
                        
                        
                        if record.name:
                            check_string = record.name.lower()
                        for word in list:
                             
                            output_string = output_string.replace(word,'')
                            check_string = check_string.replace(word,'')
                            # raise UserError((record.name.lower()))
                            if record.name and (check_string == output_string):
                                duplicate_name = record.name
                                duplicate = 1
                    # raise UserError((duplicate))
                    if duplicate == 1:
                        raise UserError((duplicate_name + " is already exist."))
                    else:
                        vals['buyer_rank'] = 1
                elif is_brand and 'brand_rank' not in vals:
                    output_string = vals['name'].lower()
                    for record in exists:
                        # mapping_table = str.maketrans({'LIMITED':'','.':''})
                        
                        
                        if record.name:
                            check_string = record.name.lower()
                        for word in list:
                             
                            output_string = output_string.replace(word,'')
                            check_string = check_string.replace(word,'')
                            # raise UserError((record.name.lower()))
                            if record.name and (check_string == output_string):
                                duplicate_name = record.name
                                duplicate = 1
                    # raise UserError((duplicate))
                    if duplicate == 1:
                        raise UserError((duplicate_name + " is already exist."))
                    else:
                        vals['brand_rank'] = 1
                elif is_customer_group and 'customer_group_rank' not in vals:
                    output_string = vals['name'].lower()
                    for record in exists:
                        # mapping_table = str.maketrans({'LIMITED':'','.':''})
                        
                        
                        if record.name:
                            check_string = record.name.lower()
                        for word in list:
                             
                            output_string = output_string.replace(word,'')
                            check_string = check_string.replace(word,'')
                            # raise UserError((record.name.lower()))
                            if record.name and (check_string == output_string):
                                duplicate_name = record.name
                                duplicate = 1
                    # raise UserError((duplicate))
                    if duplicate == 1:
                        raise UserError((duplicate_name + " is already exist."))
                    else:
                        vals['customer_group_rank'] = 1        
                    
        return super().create(vals_list)


    # def _get_name_search_order_by_fields(self):
    #     res = super()._get_name_search_order_by_fields()
    #     partner_search_mode = self.env.context.get('res_partner_search_mode')
    #     if not partner_search_mode in ('customer', 'supplier', 'buyer'):
    #         raise UserError(( res))
    #         return res
            
    #     order_by_field = 'COALESCE(res_partner.%s, 0) DESC,'
    #     if partner_search_mode == 'customer':
    #         field = 'customer_rank'
    #     if partner_search_mode == 'supplier':
    #         field = 'supplier_rank'
    #     else partner_search_mode == 'buyer':
    #         field = 'buyer_rank'
        
    #     order_by_field = order_by_field % field
        
    #     return '%s, %s' % (res, order_by_field % field) if res else order_by_field

    # def _increase_rank(self, field, n=1):
    #     if self.ids and field in ['customer_rank', 'supplier_rank', 'buyer_rank']:
    #         try:
    #             with self.env.cr.savepoint(flush=False):
    #                 query = sql.SQL("""
    #                     SELECT {field} FROM res_partner WHERE ID IN %(partner_ids)s FOR UPDATE NOWAIT;
    #                     UPDATE res_partner SET {field} = {field} + %(n)s
    #                     WHERE id IN %(partner_ids)s
    #                 """).format(field=sql.Identifier(field))
    #                 self.env.cr.execute(query, {'partner_ids': tuple(self.ids), 'n': n})
    #                 for partner in self:
    #                     self.env.cache.remove(partner, partner._fields[field])
    #         except DatabaseError as e:
    #             if e.pgcode == '55P03':
    #                 _logger.debug('Another transaction already locked partner rows. Cannot update partner ranks.')
    #             else:
    #                 raise e


    
    