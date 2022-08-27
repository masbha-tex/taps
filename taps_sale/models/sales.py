# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from datetime import datetime, timedelta
from functools import partial
from itertools import groupby

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang
from odoo.osv import expression
from odoo.tools import float_is_zero, float_compare
from odoo.tools.safe_eval import safe_eval
import re


from werkzeug.urls import url_encode

class Replenishment(models.Model):
    _inherit = "stock.warehouse.orderpoint"
    
    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order', readonly=True)
    #bom_id = fields.Many2one('mrp.bom', string='BOM', readonly=True)
    
    @api.model
    def action_open_orderpoints(self):
        fsdf = 'sfe'
        #return self._get_orderpoint_action()


class SaleOrder(models.Model):
    _inherit = "sale.order"
        
    def action_confirm(self):
        if self._get_forbidden_state_confirm() & set(self.mapped('state')):
            raise UserError(_(
                'It is not allowed to confirm an order in the following states: %s'
            ) % (', '.join(self._get_forbidden_state_confirm())))

        for order in self.filtered(lambda order: order.partner_id not in order.message_partner_ids):
            order.message_subscribe([order.partner_id.id])
        self.write(self._prepare_confirmation_values())
        bom = self.env['mrp.bom']
        for orderline in self.order_line:
            #bom = self.env['mrp.bom'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id)])
            or_line = self.env['sale.order.line'].search([('product_id', '=', orderline.product_id.id),('slidercodesfg', '=', orderline.slidercodesfg),('dyedtape', '=', orderline.dyedtape),('ptopfinish', '=', orderline.ptopfinish),('pbotomfinish', '=', orderline.pbotomfinish),('ppinboxfinish', '=', orderline.ppinboxfinish),('dippingfinish', '=', orderline.dippingfinish),('sizein', '=', orderline.sizein),('sizecm', '=', orderline.sizecm),('gap', '=', orderline.gap)]) 
            #raise UserError((len(or_line)))
            #raise UserError((orderline))
            if len(or_line)>1:
                continue
            else:
                bom_info = {
                    'code':'',
                    'active':True,
                    'type':'normal',
                    'product_tmpl_id':orderline.product_id.product_tmpl_id.id,
                    'product_id':'',
                    'product_qty':1,
                    'product_uom_id':orderline.product_id.product_tmpl_id.uom_id.id,
                    'sequence':'',
                    'ready_to_produce':'asap',
                    'picking_type_id':'',
                    'company_id':self.company_id.id,
                    'consumption':'warning',#expatt.store_fname,
                }
                bomrec = self.env['mrp.bom'].create(bom_info)
                #orderline.write({'bom_id':bomrec.id})
                #bom_line = self.env['mrp.bom']
                
                seq = 0
                if orderline.slidercodesfg:
                    seq = seq + 1
                    product_temp = self.env['product.template'].search([('name', '=', orderline.slidercodesfg)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)])
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':1,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                
                if orderline.dyedtape:
                    seq = seq + 1
                    size_type = "inch"
                    size = 0
                    tapewaight = 0.0
                    if orderline.sizein == "N/A":
                        size_type = "cm"
                        size = orderline.sizecm
                    else:
                        size = orderline.sizein
                    product_temp = self.env['product.template'].search([('name', '=', orderline.dyedtape)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                    
                    product_main = self.env['product.product'].search([('product_tmpl_id', '=', orderline.product_id.product_tmpl_id.id),('active','=',False)]).sorted(key = 'id', reverse=False)[:1]
                    formula = self.env['fg.product.formula'].search([('product_id', '=', product_main.id),('unit_type', '=', size_type)])
                    #result = contract.basic
                    formula_ = formula.amount_python_compute
                    #raise UserError((orderline.product_id.product_tmpl_id.id,product_main.id))
                    tapewaight = safe_eval(formula_, {'s': size, 'g': orderline.gap})# or 0.0, None, mode='exec', nocopy=True
                    tapewaight = round(tapewaight,4)
                    
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':tapewaight,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                    
                    
                if orderline.ptopfinish:
                    seq = seq + 1
                    product_temp = self.env['product.template'].search([('name', 'like', orderline.ptopfinish)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':1,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                    

                if orderline.pbotomfinish:
                    seq = seq + 1
                    product_temp = self.env['product.template'].search([('name', 'like', orderline.pbotomfinish)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                    
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':1,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                    
                if orderline.ppinboxfinish:
                    seq = seq + 1
                    product_temp = self.env['product.template'].search([('name', 'like', orderline.ppinboxfinish)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':1,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                
                if orderline.dippingfinish:
                    seq = seq + 1
                    product_temp = self.env['product.template'].search([('name', 'like', orderline.dippingfinish)]).sorted(key = 'id', reverse=True)[:1]
                    product_ = self.env['product.product'].search([('product_tmpl_id', '=', product_temp.id)]).sorted(key = 'id', reverse=False)[:1]
                    #raise UserError((orderline.dippingfinish,product_temp.id))
                    bom_line_info = {
                        'product_id':product_.id,
                        'company_id':self.company_id.id,
                        'product_qty':1,
                        'product_uom_id':product_temp.uom_id.id,
                        'sequence':seq,
                        'bom_id':bomrec.id,
                        'operation_id':'',
                    }
                    self.env['mrp.bom.line'].create(bom_line_info)
                    
                orderline.write({'bom_id':bomrec.id})

        # Context key 'default_name' is sometimes propagated up to here.
        # We don't need it and it creates issues in the creation of linked records.
        context = self._context.copy()
        context.pop('default_name', None)
        
        self.with_context(context)._action_confirm()
        if self.env.user.has_group('sale.group_auto_done_setting'):
            self.action_done()
        
        
        #sale_order_id sale_order_line bom_id
        return True

    def write(self):
        if self.state == 'sale':
            for or_line in self.order_line:
                replenish = self.env['stock.warehouse.orderpoint'].search([
                    ('product_id', '=', or_line.product_id.id),
                    ('sale_order_id', '=', ''),
                    ('sale_order_line', '=', '')
                ]).sorted(key = 'attribute_id', reverse = True)[:1]
                replenish.write({'sale_order_id':or_line.order_id.id,'sale_order_line':or_line.id})
            

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    
    topbottom = fields.Text(string='Top/Bottom', store=True)
    slidercode = fields.Text(string='Slider Code', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    sizemm = fields.Text(string='Size (MM)', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', store=True)
    pbotomfinish = fields.Text(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', store=True)
    gap = fields.Text(string='Gap', store=True)
    
    logoref = fields.Text(string='Logo & Ref', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    bom_id = fields.Integer('Bom Id')
    

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return
        valid_values = self.product_id.product_tmpl_id.valid_product_template_attribute_line_ids.product_template_value_ids
        # remove the is_custom values that don't belong to this template
        
        for pacv in self.product_custom_attribute_value_ids:
            if pacv.custom_product_template_attribute_value_id not in valid_values:
                self.product_custom_attribute_value_ids -= pacv
        
        # remove the no_variant attributes that don't belong to this template
        
        for ptav in self.product_no_variant_attribute_value_ids:
            if ptav._origin not in valid_values:
                self.product_no_variant_attribute_value_ids -= ptav
        
        vals = {}
        #raise UserError((self.product_no_variant_attribute_value_ids))
        
        #raise UserError((att_val))

        if not self.product_uom or (self.product_id.uom_id.id != self.product_uom.id):
            vals['product_uom'] = self.product_id.uom_id
            vals['product_uom_qty'] = self.product_uom_qty or 1.0

        lang = get_lang(self.env, self.order_id.partner_id.lang).code
        product = self.product_id.with_context(
            lang=lang,
            partner=self.order_id.partner_id,
            quantity=vals.get('product_uom_qty') or self.product_uom_qty,
            date=self.order_id.date_order,
            pricelist=self.order_id.pricelist_id.id,
            uom=self.product_uom.id
        )

        vals.update(name=self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product))
        
        #raise UserError((self.product_id.combination_indices))
        #productname = self.with_context(lang=lang).get_sale_order_line_multiline_description_sale(product)
        test_string = str(self.product_id.combination_indices)
        temp = re.findall(r'\d+', test_string)
        res = list(map(int, temp))
        atv = self.env['product.template.attribute.value'].search([('id', 'in', res)])
        
        for rec in atv:
            if rec.attribute_id.name == 'Top / Bottom':
                self.topbottom = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Slider Code':
                self.slidercode = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Slider Code (SFG)':
                self.slidercodesfg = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Finish':
                self.finish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Shade':
                self.shade = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Size (Inch)':
                self.sizein = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Size (CM)':
                self.sizecm = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Size (MM)':
                self.sizemm = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Dyed Tape':
                self.dyedtape = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Top Finish':
                self.ptopfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Bottom Finish':
                self.pbotomfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Plated Pin-Box Finish':
                self.ppinboxfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Dipping Finish':
                self.dippingfinish = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Gap':
                self.gap = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Logo & Ref':
                self.logoref = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Shape Finish':
                self.shapefin = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'BCD Part Material Type / Size':
                self.bcdpart = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Nail Material / Type / Shape / Size':
                self.nailmat = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Nail Cap Logo':
                self.nailcap = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == 'Finish Name ( BCD/NAIL/ NAIL CAP)':
                self.fnamebcd = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == '1 NO. Washer Material & Size':
                self.nu1washer = rec.product_attribute_value_id.name
                continue
            if rec.attribute_id.name == '2 NO. Washer Material & Size':
                self.nu2washer = rec.product_attribute_value_id.name
                continue
        
#         if productname and productname.find("(")>0:
#             b = productname
#             c = len(b)
#             d = b.index("(")
#             e = b.index(")")
#             f = c-d-1
#             g = c-e
#             h = b[-f:-g]
#             for kv in h.split(","):
#                 atv = self.env['product.attribute.value'].search([('name', '=', kv.strip())])
#                 satv = atv.sorted(key = 'attribute_id')[:1]
#                 at = self.env['product.attribute'].search([('id', '=', int(satv.attribute_id))])
#                 if at.name == 'Top / Bottom':
#                     self.topbottom = kv
#                     continue
#                 if at.name == 'Slider Code':
#                     self.slidercode = kv
#                     continue
#                 if at.name == 'Slider Code (SFG)':
#                     self.slidercodesfg = kv
#                     continue
#                 if at.name == 'Finish':
#                     self.finish = kv
#                     continue
#                 if at.name == 'Shade':
#                     self.shade = kv
#                     continue
#                 if at.name == 'Size (Inch)':
#                     self.sizein = kv
#                     continue
#                 if at.name == 'Size (CM)':
#                     self.sizecm = kv
#                     continue
#                 if at.name == 'Size (MM)':
#                     self.sizemm = kv
#                     continue
#                 if at.name == 'Dyed Tape':
#                     self.dyedtape = kv
#                     continue
#                 if at.name == 'Plated Top Finish':
#                     self.ptopfinish = kv
#                     continue
#                 if at.name == 'Plated Bottom Finish':
#                     self.pbotomfinish = kv
#                     continue
#                 if at.name == 'Plated Pin-Box Finish':
#                     self.ppinboxfinish = kv
#                     continue
#                 if at.name == 'Dipping Finish':
#                     self.dippingfinish = kv
#                     continue
#                 if at.name == 'Gap':
#                     self.gap = kv
#                     continue
#                 if at.name == 'Logo & Ref':
#                     self.logoref = kv
#                     continue
#                 if at.name == 'Shape Finish':
#                     self.shapefin = kv
#                     continue
#                 if at.name == 'BCD Part Material Type / Size':
#                     self.bcdpart = kv
#                     continue
#                 if at.name == 'Nail Material / Type / Shape / Size':
#                     self.nailmat = kv
#                     continue
#                 if at.name == 'Nail Cap Logo':
#                     self.nailcap = kv
#                     continue
#                 if at.name == 'Finish Name ( BCD/NAIL/ NAIL CAP)':
#                     self.fnamebcd = kv
#                     continue
#                 if at.name == '1 NO. Washer Material & Size':
#                     self.nu1washer = kv
#                     continue
#                 if at.name == '2 NO. Washer Material & Size':
#                     self.nu2washer = kv
#                     continue   
                        
                #raise UserError((h)) product_attribute_value attribute_id Size (Inch/cm)      

        self._compute_tax_id()
        if self.order_id.pricelist_id and self.order_id.partner_id:
            vals['price_unit'] = product._get_tax_included_unit_price(
                self.company_id,
                self.order_id.currency_id,
                self.order_id.date_order,
                'sale',
                fiscal_position=self.order_id.fiscal_position_id,
                product_price_unit=self._get_display_price(product),
                product_currency=self.order_id.currency_id
            )
        self.update(vals)

        title = False
        message = False
        result = {}
        warning = {}
        if product.sale_line_warn != 'no-message':
            title = _("Warning for %s", product.name)
            message = product.sale_line_warn_msg
            warning['title'] = title
            warning['message'] = message
            result = {'warning': warning}
            if product.sale_line_warn == 'block':
                self.product_id = False

        return result   
    


    def get_sale_order_line_multiline_description_sale(self, product):
        """ Compute a default multiline description for this sales order line.

        In most cases the product description is enough but sometimes we need to append information that only
        exists on the sale order line itself.
        e.g:
        - custom attributes and attributes that don't create variants, both introduced by the "product configurator"
        - in event_sale we need to know specifically the sales order line as well as the product to generate the name:
          the product is not sufficient because we also need to know the event_id and the event_ticket_id (both which belong to the sale order line).
        """
        return product.get_product_multiline_description_sale()# + self._get_sale_order_line_multiline_description_variants()