import datetime
import math


from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ManufacturingOrder(models.Model):
    _name = "fg.packing"
    _description = "Fg Packing"
    _check_company_auto = True


    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True, check_company=True)    
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True, default=lambda self: self.env.company.id, check_company=True)

    #Product Details 
    oa_id = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True) #oa Number

    def _get_oa_information(self, docids, data=None):
        domain = []
        if data.get('oa_number'):
            domain.append(('oa_id', '=', data.get('oa_number')))
        
        
        docs = self.env['operation.packing'].sudo().search(domain, order='id desc',limit=1)
        
        # store_label = self.env['label.print.data'].sudo().create({'name':docs.name,'batch_lot':data.get('batch_lot'),
        #                                                           'table_name':data.get('table_name'),
        #                                                           'qc_by':data.get('qc_person'),
        #                                                           'pre_check_by':data.get('pre_check_person'),
        #                                                           'print_by':data.get('printing_person'),
        #                                                           'label_qty':data.get('label_qty'),
        #                                                           'label_copy':data.get('copy_of_print')})     
        
        common_data = [
            data.get('logo'), #0
            data.get('company_name'), #1
            data.get('company_address'), #2
            data.get('table_name'), #3
            data.get('date'), #4
            data.get('batch_lot'), #5
            data.get('oa_number'), #6
            data.get('iteam'), #7
            data.get('finish'), #8
            data.get('shade'), #9
            data.get('size'), #10
            data.get('qc_person'), #11
            data.get('pre_check_person'),#12
            data.get('printing_person'),#13
            data.get('qty'), #14
            data.get('label_qty'), #15
            data.get('copy_of_print'), #16
            data.get('Country_name'), #17
            data.get(docs.partner_id.name), #18 Customer Name
            # data.get(docs.name), #15
                     
        ]
        common_data.append(common_data)
        # raise UserError(docs.partner_id)  
        
        return {
            'doc_ids': docs.ids,
            'doc_model': 'operation.packing',
            'docs': docs,
            'datas': common_data,
            
        }
    
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True) #Customer Name
    buyer_name = fields.Char(string='Buyer', readonly=True) # Buyer Name 
    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True) 
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)]) #Product name Full
    fg_categ_type = fields.Char(related='product_template_id.fg_categ_type.name', string='Item', store=True) #Product name Short