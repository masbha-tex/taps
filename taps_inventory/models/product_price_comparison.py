import logging
from odoo import fields, models, tools, api, _
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class ProductPriceComparison(models.Model):
    _name = "product.price.comparison"
    _description = "Product Price Comparison"
    _check_company_auto = True
    
    product_id = fields.Many2one('product.product', string='Item', readonly=False, store=True)
    product_template_id = fields.Many2one('product.template', string='Product', related="product_id.product_tmpl_id",  store=True)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_template_id.uom_id')
    pr_code = fields.Char(string='Item Code', store=True)
    product_category = fields.Many2one('category.type', string='Category')
    parent_category = fields.Many2one('category.type', string='Product Type')
    comparison_month = fields.Char(string='Comparison Month', store=True)
    s_last_currency = fields.Many2one('res.currency', string='Currency', readonly=False, store=True)
    second_last_price = fields.Float(string='Second Last Price', readonly=False)
    last_currency = fields.Many2one('res.currency', string='Last Currency', readonly=False, store=True)
    last_price = fields.Float(string='Last Price', readonly=False)
    
    qty = fields.Float(related='product_template_id.qty_available', string='Qty On Hand', readonly=True)
    company_id = fields.Many2one('res.company', 'Company', related='product_id.company_id', readonly=True, index=True, default=lambda self: self.env.company.id)



    # def _compute_prices(self):
    #     for rec in self:
    #         purchase_line = self.env['purchase.order.line'].sudo().search([('state','=','purchase'),('product_id.id','=',rec.product_variant_id.id)],order='id desc',limit=2)
    #         if purchase_line:
    #             if len(purchase_line) == 1:
    #                 rec.last_price = round((purchase_line.price_unit / purchase_line.order_id.currency_rate),4)
    #                 rec.second_last_price = round((purchase_line.price_unit / purchase_line.order_id.currency_rate),4)
    #             else:
    #                 rec.last_price = round((purchase_line[0].price_unit / purchase_line[0].order_id.currency_rate),4)
    #                 rec.second_last_price = round((purchase_line[1].price_unit / purchase_line[1].order_id.currency_rate),4)
    #         else:
    #             rec.last_price = round(0,4)
    #             rec.second_last_price = round(0,4)