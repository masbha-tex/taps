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
    @api.model_create_multi
    def create(self, vals_list):
        search_partner_mode = self.env.context.get('res_partner_search_mode')
        is_customer = search_partner_mode == 'customer'
        is_supplier = search_partner_mode == 'supplier'
        is_buyer = search_partner_mode == 'buyer'
        if search_partner_mode:
            for vals in vals_list:
                if is_customer and 'customer_rank' not in vals:
                    vals['customer_rank'] = 1
                elif is_supplier and 'supplier_rank' not in vals:
                    vals['supplier_rank'] = 1
                elif is_buyer and 'buyer_rank' not in vals:
                    vals['buyer_rank'] = 1
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


    
    