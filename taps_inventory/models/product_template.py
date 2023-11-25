# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class Product(models.Model):
    _inherit = "product.product"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit value", compute="_compute_landed_cost_and_unit_value", groups="stock.group_stock_manager")

    def _compute_landed_cost_and_unit_value(self):
        domain = [
            ('location_id.usage', '=', 'internal'),
            ('create_date', '<=', self.env.context.get('to_date')),
            ('lot_id', '!=', False),
            ('product_id', 'in', self.ids),
        ]

        groups = self.env['stock.quant'].read_group(domain, ['ids:array_agg(id)'], ['product_id'])

        quant_ids = [g for group in groups for g in group['ids']]

        # map the landed_cost and cache it, so landed cost will not be computed everytime
        self.env['stock.quant'].browse(quant_ids).mapped('landed_cost')

        group_dict = {group['product_id'][0]: group['ids'] for group in groups}

        for product in self:
            quant = self.env['stock.quant']
            if group_dict.get(product.id):
                quant = quant.browse(group_dict[product.id])
            product.landed_cost = sum(quant.mapped('landed_cost'))
            product.total_unit_value = sum(quant.mapped('total_unit_value'))
            product.unit_value = sum(quant.mapped('unit_value'))

    def _unlink_or_archive(self, check_access=True):
        """Unlink or archive products.
        Try in batch as much as possible because it is much faster.
        Use dichotomy when an exception occurs.
        """

        # Avoid access errors in case the products is shared amongst companies
        # but the underlying objects are not. If unlink fails because of an
        # AccessError (e.g. while recomputing fields), the 'write' call will
        # fail as well for the same reason since the field has been set to
        # recompute.
        if check_access:
            self.check_access_rights('unlink')
            self.check_access_rule('unlink')
            self.check_access_rights('write')
            self.check_access_rule('write')
            self = self.sudo()
            to_unlink = self._filter_to_unlink()
            to_archive = self - to_unlink
            # raise UserError(('b'))
            # to_archive.write({'active': False})
            self = to_unlink

        try:
            with self.env.cr.savepoint(), tools.mute_logger('odoo.sql_db'):
                self.unlink()
        except Exception:
            # We catch all kind of exceptions to be sure that the operation
            # doesn't fail.
            if len(self) > 1:
                self[:len(self) // 2]._unlink_or_archive(check_access=False)
                self[len(self) // 2:]._unlink_or_archive(check_access=False)
            else:
                if self.active:
                    # Note: this can still fail if something is preventing
                    # from archiving.
                    # This is the case from existing stock reordering rules.
                    a = ''
                    # self.write({'active': False})



class IncludeCateTypeInPT(models.Model):
    _inherit = 'product.template'
    categ_type = fields.Many2one('category.type', 'Category Type', check_company=True, change_default=True)
    
    
    generic_name = fields.Char(string="Generic Name")
    pur_description = fields.Selection([
        ('Auto Taffeta', 'Auto Taffeta'),
        ('Brass Wire', 'Brass Wire'),
        ('C#3 Long Chain', 'C#3 Long Chain'),
        ('C#3 Long Chain GRS', 'C#3 Long Chain GRS'),
        ('C#3 Special Slider', 'C#3 Special Slider'),
        ('C#3 STD Slider', 'C#3 STD Slider'),
        ('C#3 WP Long Chain', 'C#3 WP Long Chain'),
        ('C#5 Body, Cap & Spring', 'C#5 Body, Cap & Spring'),
        ('C#5 Long Chain', 'C#5 Long Chain'),
        ('C#5 Long Chain GRS', 'C#5 Long Chain GRS'),
        ('C#5 Special Slider', 'C#5 Special Slider'),
        ('C#5 STD Slider', 'C#5 STD Slider'),
        ('C#5 WP Long Chain', 'C#5 WP Long Chain'),
        ('Dipping Chemical', 'Dipping Chemical'),
        ('Dyeing', 'Dyeing'),
        ('ETP', 'ETP'),
        ('M#4  U Top stopper', 'M#4  U Top stopper'),
        ('M#4 Cotton Tape', 'M#4 Cotton Tape'),
        ('M#4 H Bottom', 'M#4 H Bottom'),
        ('M#4 Special Slider', 'M#4 Special Slider'),
        ('M#4 STD Slider', 'M#4 STD Slider'),
        ('M#4 Tape DN+', 'M#4 Tape DN+'),
        ('M#4 Tape GRS', 'M#4 Tape GRS'),
        ('M#4 Top Wire', 'M#4 Top Wire'),
        ('M#5  U Top stopper', 'M#5  U Top stopper'),
        ('M#5 Body, Cap & Spring', 'M#5 Body, Cap & Spring'),
        ('M#5 Cotton Tape', 'M#5 Cotton Tape'),
        ('M#5 H Bottom', 'M#5 H Bottom'),
        ('M#5 PIN AND BOX', 'M#5 PIN AND BOX'),
        ('M#5 Special Slider', 'M#5 Special Slider'),
        ('M#5 STD Slider', 'M#5 STD Slider'),
        ('M#5 Tape', 'M#5 Tape'),
        ('M#5 Tape GRS', 'M#5 Tape GRS'),
        ('M#8  U Top stopper', 'M#8  U Top stopper'),
        ('M#8 H Bottom', 'M#8 H Bottom'),
        ('M#8 PIN AND BOX', 'M#8 PIN AND BOX'),
        ('M#8 Polyester tape', 'M#8 Polyester tape'),
        ('M#8 Special Slider', 'M#8 Special Slider'),
        ('N#3 ALU Bottom', 'N#3 ALU Bottom'),
        ('N#3 ALU Top Wire', 'N#3 ALU Top Wire'),
        ('N#3 Ultrasonic  Bottom', 'N#3 Ultrasonic  Bottom'),
        ('N#3 Ultrasonic Top', 'N#3 Ultrasonic Top'),
        ('N#5 ALU Bottom', 'N#5 ALU Bottom'),
        ('N#5 ALU Top Wire', 'N#5 ALU Top Wire'),
        ('N#5 PIN AND BOX', 'N#5 PIN AND BOX'),
        ('N#5 Ultrasonic Bottom', 'N#5 Ultrasonic Bottom'),
        ('N#5 Ultrasonic Top', 'N#5 Ultrasonic Top'),
        ('Others Item', 'Others Item'),
        ('P#3 Polyester tape', 'P#3 Polyester tape'),
        ('P#3 Special Slider', 'P#3 Special Slider'),
        ('P#5 Polyester GRS', 'P#5 Polyester GRS'),
        ('P#5 Polyester Tape', 'P#5 Polyester Tape'),
        ('P#5 Special Slider', 'P#5 Special Slider'),
        ('P#5 STD Slider', 'P#5 STD Slider'),
        ('Paint & Chemical', 'Paint & Chemical'),
        ('Resin', 'Resin'),
        ('Scrap', 'Scrap')
    ],string='PUR Description', store=False, readonly=False, copy=True)
    gap_cm = fields.Float(string="GAP(cm & inc)", copy=True, default=None)
    gap_inch = fields.Float(string="GAP(inch)", copy=True, default=None)
    fg_categ_type = fields.Selection([
        ('AL #4 CE', 'AL #4 CE'),
        ('AL #5 CE', 'AL #5 CE'),
        ('AL #5 OE', 'AL #5 OE'),
        ('Coil #3 CE', 'Coil #3 CE'),
        ('Coil #3 Inv CE', 'Coil #3 Inv CE'),
        ('Coil #3 OE', 'Coil #3 OE'),
        ('Coil #3 Inv OE', 'Coil #3 Inv OE'),
        ('Coil #5 OE', 'Coil #5 OE'),
        ('Coil #5 CE', 'Coil #5 CE'),
        ('Coil #5 Inv CE', 'Coil #5 Inv CE'),
        ('Metal #4 CE', 'Metal #4 CE'),
        ('Metal #4 OE', 'Metal #4 OE'),
        ('Metal #5 CE', 'Metal #5 CE'),
        ('Metal #5 OE', 'Metal #5 OE'),
        ('Metal #8 OE', 'Metal #8 OE'),
        ('Metal #8 CE', 'Metal #8 CE'),
        ('Metal #10 OE', 'Metal #10 OE'),
        ('Metal #10 CE', 'Metal #10 CE'),
        ('Plastic #3 CE', 'Plastic #3 CE'),
        ('Plastic #3 OE', 'Plastic #3 OE'),
        ('Plastic #5 CE', 'Plastic #5 CE'),
        ('Plastic #5 OE', 'Plastic #5 OE'),
        ('Plastic #8 CE', 'Plastic #8 CE'),
        ('Plastic #8 OE', 'Plastic #8 OE'),
        ('Others', 'Others')
    ],string='FG Category', store=True, readonly=False, copy=False)

    pack_qty = fields.Float(string="Qty/Pack", copy=True, default=0.0)
    #description_purchase = fields.Text('Purchase Description', related='pur_description', translate=True)
    # fg_product_type = fields.Selection([
    #     ('Auto Taffeta', 'Auto Taffeta'),
    #     ('Brass Wire', 'Brass Wire'),
    #     ('Scrap', 'Scrap')
    #     ],string='PUR Description', store=True, readonly=True, copy=False)
       
    @api.onchange('pur_description')
    def onchange_pur_description(self):
        self.description_purchase = ''
        if self.pur_description !="":
            self.description_purchase = self.pur_description

# class ProductTemplateAttributeLine(models.Model):

#     _inherit = "product.template.attribute.value"
            
#     def _get_combination_name(self):
#         """Exclude values from single value lines or from no_variant attributes."""
#         ptavs = self._without_no_variant_attributes().with_prefetch(self._prefetch_ids)
#         ptavs = ptavs._filter_single_value_lines().with_prefetch(self._prefetch_ids)
#         raise UserError((ptavs))
#         return ", ".join([ptav.name for ptav in ptavs])
            
            
class ProductTemplateAttributeLine(models.Model):
    """Attributes available on product.template with their selected values in a m2m.
    Used as a configuration model to generate the appropriate product.template.attribute.value"""

    _inherit = "product.template.attribute.line"
    _rec_name = 'attribute_id'
    _description = 'Product Template Attribute Line'
    _order = 'sequence'            
            
    sequence = fields.Integer('Sequence', help="Determine the display order", index=True)
    
    def write(self, values):
        """Override to:
        - Add constraints to prevent doing changes that are not supported such
            as modifying the template or the attribute of existing lines.
        - Clean up related values and related variants when archiving or when
            updating `value_ids`.
        """
        if 'product_tmpl_id' in values:
            for ptal in self:
                if ptal.product_tmpl_id.id != values['product_tmpl_id']:
                    raise UserError(
                        _("You cannot move the attribute %s from the product %s to the product %s.") %
                        (ptal.attribute_id.display_name, ptal.product_tmpl_id.display_name, values['product_tmpl_id'])
                    )

        if 'attribute_id' in values:
            for ptal in self:
                if ptal.attribute_id.id != values['attribute_id']:
                    raise UserError(
                        _("On the product %s you cannot transform the attribute %s into the attribute %s.") %
                        (ptal.product_tmpl_id.display_name, ptal.attribute_id.display_name, values['attribute_id'])
                    )
        # Remove all values while archiving to make sure the line is clean if it
        # is ever activated again.
        if not values.get('active', True):
            values['value_ids'] = [(5, 0, 0)]
        invalidate_cache = 'sequence' in values and any(record.sequence != values['sequence'] for record in self)
        res = super(ProductTemplateAttributeLine, self).write(values)
        if 'active' in values:
            self.flush()
            self.env['product.template'].invalidate_cache(fnames=['attribute_line_ids'])
            #self.invalidate_cache()
        # If coming from `create`, no need to update the values and the variants
        # before all lines are created.
        if self.env.context.get('update_product_template_attribute_values', True):
            self._update_product_template_attribute_values()
        return res    
    
#     def write(self, vals):
#         """Override to make sure attribute type can't be changed if it's used on
#         a product template.

#         This is important to prevent because changing the type would make
#         existing combinations invalid without recomputing them, and recomputing
#         them might take too long and we don't want to change products without
#         the user knowing about it."""
#         if 'create_variant' in vals:
#             for pa in self:
#                 if vals['create_variant'] != pa.create_variant and pa.is_used_on_products:
#                     raise UserError(
#                         _("You cannot change the Variants Creation Mode of the attribute %s because it is used on the following products:\n%s") %
#                         (pa.display_name, ", ".join(pa.product_tmpl_ids.mapped('display_name')))
#                     )
#         invalidate_cache = 'sequence' in vals and any(record.sequence != vals['sequence'] for record in self)
#         res = super(ProductAttribute, self).write(vals)
#         if invalidate_cache:
#             # prefetched o2m have to be resequenced
#             # (eg. product.template: attribute_line_ids)
#             self.flush()
#             self.invalidate_cache()
#         return res    
class StockQuant(models.Model):
    _inherit = "stock.quant"

    landed_cost = fields.Monetary(string="Landed cost", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    total_unit_value = fields.Monetary(string="Total Unit Value", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    unit_value = fields.Monetary(string="Unit Value", compute="_compute_landed_cost", groups="stock.group_stock_manager")
    product_category = fields.Many2one("product.category", related="product_id.categ_id", store=True)

    def _compute_landed_cost(self):
        groups = self.read_group([('location_id.usage', '=', 'internal'), ('lot_id', 'in', self.lot_id.ids)], ['quantity:sum'], ['lot_id'])
        group_dict = {group['lot_id'][0]: group['quantity'] for group in groups}

        for quant in self:
            quantity = group_dict[quant.lot_id.id] if quant.lot_id else 0
            company_id = quant.company_id

            quant.landed_cost = (quant.quantity / quantity) * quant.lot_id.landed_cost_total if quantity != 0 else 0
            quant.unit_value = (quant.value - quant.landed_cost) / quant.quantity if quant.quantity != 0 else 0
            quant.total_unit_value = quant.value / quant.quantity if quant.quantity != 0 else 0