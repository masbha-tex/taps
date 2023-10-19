from odoo import fields, models
from odoo.exceptions import UserError, ValidationError


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
            to_archive.write({'active': False})
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
                    
