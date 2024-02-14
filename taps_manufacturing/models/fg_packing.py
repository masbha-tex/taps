import datetime
import math


from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ManufacturingOrder(models.Model):
    _name = "fg.packing"
    _description = "Fg Packing"
    _check_company_auto = True


    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True, check_company=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', readonly=True, store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    company_id = fields.Many2one('res.company', string='Company', readonly=True, store=True, index=True, default=lambda self: self.env.company.id, check_company=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Char(related='product_template_id.fg_categ_type.name', string='Item', store=True)