import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError

from fuzzywuzzy import fuzz

class BuyerName(models.Model):
    _name = 'sale.buyer'
    _rec_name= 'name'
    _description = 'Buyer List'
    
    name = fields.Char(string='Buyer Name')

class ResPartner(models.Model):
    _inherit = 'res.partner'

    buyer_rank = fields.Integer(default=0, copy=False)
    brand_rank = fields.Integer(default=0, copy=False)
    sale_representative = fields.Many2one('sale.representative', string="Sale Representative")
    related_buyer = fields.Many2one('res.partner', string="Related Buyer")
    related_customer = fields.Many2one('res.partner', string="Related Customer")
    contact_person = fields.Char(string="Contact Person")
    contact_mobile = fields.Char(string="Contact Person's Mobile")
    
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
        
    @api.onchange('phone')
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
        # raise UserError((vals_list))
        # if is_customer:
        #     exists = self.env['res.partner'].search([('customer_rank', '>=', 1)])
        # if is_buyer:
        #     exists = self.env['res.partner'].search([('buyer_rank', '>=', 1)])
        # if is_brand:
        #     exists = self.env['res.partner'].search([('brand_rank', '>=', 1)])
        
            
            
            
        if search_partner_mode:
            for vals in vals_list:
                if is_customer and 'customer_rank' not in vals:
                    # for record in exists:
                    #     # mapping_table = str.maketrans({'LIMITED':'','.':''})
                    #     list = ['LIMITED','.']
                    #     translation_table = str.maketrans({char: None for char in ''.join(list)})
                    #     output_string = vals['name'].translate(translation_table)
                        
                    #     raise UserError((output_string))
                        
                    vals['customer_rank'] = 1
                elif is_supplier and 'supplier_rank' not in vals:
                    vals['supplier_rank'] = 1
                elif is_buyer and 'buyer_rank' not in vals:
                    vals['buyer_rank'] = 1
                elif is_brand and 'brand_rank' not in vals:
                    vals['brand_rank'] = 1
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


    
    