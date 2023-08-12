# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import AccessError, UserError, ValidationError

class IncludeCateTypeInPT(models.Model):
    _inherit = 'product.template'
    categ_type = fields.Many2one('category.type', 'Category Type', check_company=True, change_default=True)
    
    
    generic_name = fields.Char(String="Generic Name")
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
        ('AL #5 CE', 'AL #5 CE'),
        ('Coil #3 CE', 'Coil #3 CE'),
        ('Coil #5 OE', 'Coil #5 OE'),
        ('Coil #5 CE', 'Coil #5 CE'),
        ('Metal #4 CE', 'Metal #4 CE'),
        ('Metal #5 CE', 'Metal #5 CE'),
        ('Metal #5 OE', 'Metal #5 OE'),
        ('Metal #8 OE', 'Metal #8 OE'),
        ('Plastic #3 CE', 'Plastic #3 CE'),
        ('Plastic #3 OE', 'Plastic #3 OE'),
        ('Plastic #5 CE', 'Plastic #5 CE'),
        ('Plastic #5 OE', 'Plastic #5 OE')
    ],string='FG Category', store=True, readonly=False, copy=False)
    #description_purchase = fields.Text('Purchase Description', related='pur_description', translate=True)
    # fg_product_type = fields.Selection([
    #     ('Auto Taffeta', 'Auto Taffeta'),
    #     ('Brass Wire', 'Brass Wire'),
    #     ('Scrap', 'Scrap')
    #     ],string='PUR Description', store=True, readonly=True, copy=False)
    
 
#  Plastic #5 CE
#  Coil #5 OE
#  Coil #5 CE
#  Coil #3 CE
#  Plastic #5 OE
#  AL #5 CE
#  Plastic #3 CE
#  Metal #4 CE
#  Metal #5 OE
#  Metal #5 CE
# Metal #8 OE
        
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
        a = 'a'
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