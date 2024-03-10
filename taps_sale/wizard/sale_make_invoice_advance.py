import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInvCustom(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            moves = sale_orders._create_invoices(final=self.deduct_down_payments)
            
            # btn_order = sale_orders.filtered(lambda x: x.company_id.id == 3)
            # # order_ref = btn_order.mapped('order_ref')
            
            # if btn_order:
            #     pi_line = self.env['sale.order.line'].search([('order_id','in',btn_order.order_ref.ids)])
            #     moulds = pi_line.filtered(lambda x: x.product_template_id.name == 'MOULD' and x.price_subtotal >= 0)
            #     if moulds:
            #         for m in moulds:
            #             b_moves = moves.filtered(lambda x: x.company_id.id == 3)
            #             ac_line = self.env['account.move.line'].search([('move_id','=',b_moves.id)])
            #             if ac_line:
            #                 # raise UserError((ac_line[1].account_id.id))
            #                 eoij = ac_line.write({'move_id':b_moves.id,'product_id':m.product_id.id,'product_uom_id': m.product_uom.id,'quantity': m.product_uom_qty,'price_unit': m.price_unit,'price_subtotal': m.price_subtotal,'account_id':ac_line[0].account_id.id,'account_root_id':ac_line[0].account_root_id.id,'analytic_account_id': ac_line[0].analytic_account_id.id})
                            
                            # raise UserError(('uuuj')) ,'account_id':ac_line[0].account_id.id,'account_root_id':ac_line[0].account_root_id.id
                            # account_id | account_root_id
                        # moves.invoice_line_ids.create({'product_id':m.product_id})
            #     btn_order.filtered(lambda x: x.company_id.id == 3)
            # moves.action_post()
            if moves:
                # for mv in moves:
                invoice_vals_list = []
                invoice_vals = self._prepare_invoice(moves)

                invoice_line_vals = []
                down_payment_section_added = False
                for mv in moves:
                    for line in mv.invoice_line_ids:
                        invoice_line_vals.append((0, 0, self._prepare_invoice_line(line,)),)
                        # invoice_item_sequence += 1
                
                invoice_vals['line_id'] += invoice_line_vals
                invoice_vals_list.append(invoice_vals)
                
                com_in = self.env['combine.invoice'].sudo().create(invoice_vals_list)
                # .with_context(default_move_type='out_invoice')
        else:
            # Create deposit product if necessary
            if not self.product_id:
                vals = self._prepare_deposit_product()
                self.product_id = self.env['product.product'].create(vals)
                self.env['ir.config_parameter'].sudo().set_param('sale.default_deposit_product_id', self.product_id.id)

            sale_line_obj = self.env['sale.order.line']
            for order in sale_orders:
                amount, name = self._get_advance_details(order)

                if self.product_id.invoice_policy != 'order':
                    raise UserError(_('The product used to invoice a down payment should have an invoice policy set to "Ordered quantities". Please update your deposit product to be able to create a deposit invoice.'))
                if self.product_id.type != 'service':
                    raise UserError(_("The product used to invoice a down payment should be of type 'Service'. Please use another product or update this product."))
                taxes = self.product_id.taxes_id.filtered(lambda r: not order.company_id or r.company_id == order.company_id)
                tax_ids = order.fiscal_position_id.map_tax(taxes, self.product_id, order.partner_shipping_id).ids
                analytic_tag_ids = []
                for line in order.order_line:
                    analytic_tag_ids = [(4, analytic_tag.id, None) for analytic_tag in line.analytic_tag_ids]

                so_line_values = self._prepare_so_line(order, analytic_tag_ids, tax_ids, amount)
                so_line = sale_line_obj.create(so_line_values)
                self._create_invoice(order, so_line, amount)
        if self._context.get('open_invoices', False):
            return sale_orders.action_view_invoice()
        return {'type': 'ir.actions.act_window_close'}



    def _prepare_invoice(self,moves):
        z_invoice = m_invoice = None
        for mv in moves:
            if mv.company_id.id == 1:
                z_invoice = mv.id
            else:
                m_invoice = mv.id
        self.ensure_one()
        
        invoice_vals = {
            'name':'New',
            'currency_id':moves[0].currency_id.id,
            'line_id':[],
            'partner_id':moves[0].partner_id.id,
            'partner_bank_id':moves[0].partner_bank_id.id,
            'payment_reference':moves[0].payment_reference,
            'invoice_date':moves[0].invoice_date,
            'invoice_payment_term_id':moves[0].invoice_payment_term_id.id,
            'invoice_incoterm_id':moves[0].invoice_incoterm_id.id,
            'z_invoice':z_invoice,
            'm_invoice':m_invoice,
            'state':moves[0].state,
        }
        return invoice_vals


    def _prepare_invoice_line(self, line):#**optional_values,
        # self.ensure_one()
        res = {
            'invoice_id':line.move_id.id,
            'sale_order_line':line.sale_line_ids.id,
            'account_move_line':line.id,
            'parent_state':line.move_id.state,
            'sequence':line.sequence,
            'currency_id':line.currency_id.id,
            'product_uom_id':line.product_uom_id.id,
            'product_id':line.product_id.id,
            'product_uom_category_id':line.product_uom_category_id.id,
            'quantity':line.quantity,
            'price_unit':line.price_unit,
            'discount':line.discount,
            'price_subtotal':line.price_subtotal,
            'price_total':line.price_total
            }
        # if optional_values:
        #     res.update(optional_values)
        # if self.display_type:
        #     res['account_id'] = False
        return res