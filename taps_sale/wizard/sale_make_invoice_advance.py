import time

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class SaleAdvancePaymentInvCustom(models.TransientModel):
    _inherit = "sale.advance.payment.inv"

    def create_invoices(self):
        sale_orders = self.env['sale.order'].browse(self._context.get('active_ids', []))
        if self.advance_payment_method == 'delivered':
            moves = sale_orders._create_invoices(final=self.deduct_down_payments)
            
            #----- Start for Mould --------#
            # btn_order = sale_orders.filtered(lambda x: x.company_id.id == 3)
            # order_ref = btn_order.mapped('order_ref')
            
            # if btn_order:
            #     pi_line = self.env['sale.order.line'].search([('order_id','in',btn_order.order_ref.ids)])
            #     moulds = pi_line.filtered(lambda x: x.product_template_id.name == 'MOULD' and x.price_subtotal >= 0)
            #     invoice_vals_w = {'line_id':[]}
            #     if moulds:
            #         value = sum(moulds.mapped('price_subtotal'))
            #         b_moves = moves.filtered(lambda x: x.company_id.id == 3)
            #         ac_line = self.env['account.move.line'].search([('move_id','=',b_moves.id)])
            #         inv_line = ac_line.filtered(lambda x: 'INV/' in x.name)
            #         # raise UserError((inv_line.debit,value))
            #         # inv_line.write({'debit': inv_line.debit + value})
            #         invoice_line_vals_w = []
            #         for m in moulds:
            #             # b_moves.write('move_line':)
            #             if ac_line:
            #                 line_data = {'move_id':b_moves.id,'product_id':m.product_id.id,'product_uom_id': m.product_uom.id,'quantity': m.product_uom_qty,'price_unit': m.price_unit,'price_subtotal': m.price_subtotal,'debit':0,'credit':m.price_subtotal}
            #                 # eoij = ac_line.write({'move_id':b_moves.id,'product_id':m.product_id.id,'product_uom_id': m.product_uom.id,'quantity': m.product_uom_qty,'price_unit': m.price_unit,'price_subtotal': m.price_subtotal,'debit':0,'credit':m.price_subtotal})
            #                 invoice_line_vals_w.append(line_data)
            #         invoice_vals_list_w = []
            #         invoice_vals_w['line_id'] += invoice_line_vals_w
            #         invoice_vals_list_w.append(invoice_vals_w)
            #         raise UserError((invoice_vals_list_w[0]))
            #         com_update = b_moves.sudo().update(invoice_vals_list_w)
            #----- End for Mould --------#
            
            moves.action_post()
            if moves:
                # raise UserError(('erterter'))
                # for mv in moves:
                invoice_vals_list = []
                # exist_com_in = self.env['combine.invoice'].sudo().search([('m_invoice.id','in',moves.ids)])
                # if exist_com_in:
                #     invoice_vals = self._prepare_invoice_for_update(moves)
                # else:
                invoice_vals = self._prepare_invoice(moves)

                invoice_line_vals = []
                down_payment_section_added = False
                for mv in moves:
                    for line in mv.invoice_line_ids:
                        invoice_line_vals.append((0, 0, self._prepare_invoice_line(line,)),)
                        # invoice_item_sequence += 1
                btn_order = sale_orders.filtered(lambda x: x.company_id.id == 3)
                order_ref = btn_order.mapped('order_ref')
                if not order_ref:
                    order_ref = btn_order.mapped('id')
                    
            
                if btn_order:
                    pi_line = self.env['sale.order.line'].search([('order_id','in',btn_order.order_ref.ids)])
                    moulds = pi_line.filtered(lambda x: x.product_template_id.name == 'MOULD' and x.price_subtotal >= 0)
                    if moulds:
                        qty = sum(moulds.mapped('product_uom_qty'))
                        value = sum(moulds.mapped('price_subtotal'))
                        invoice_line_vals.append((0, 0, self._prepare_mould(qty,value)),)
                        # b_moves = moves.filtered(lambda x: x.company_id.id == 3)
                        # ac_line = self.env['account.move.line'].search([('move_id','=',b_moves.id)])
                        # inv_line = ac_line.filtered(lambda x: 'INV/' in x.name)
                        # raise UserError((inv_line.debit,value))
                        # inv_line.write({'debit': inv_line.debit + value})
                        # invoice_line_vals_w = []
                        # for m in moulds:

                        
                invoice_vals['line_id'] += invoice_line_vals
                invoice_vals_list.append(invoice_vals)
                # raise UserError((com_line_data.sale_line_ids))
                
                # if exist_com_in:
                #     raise UserError(('feef'))
                #     exist_com_in.sudo().write(invoice_vals_list)
                # else:
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
        z_invoice = m_invoice =  hs_code = beneficiary = None
        pi_numbers = po_numbers = style_ref =""
        for mv in moves:
            if mv.company_id.id == 1:
                hs_code = '9607.11.00'
                z_invoice = mv.id
                order_list = [str(i) for i in sorted(mv.invoice_origin.split(','))]
                i = 0
                for order in order_list:
                    order = order.strip()
                    com_in = self.env['sale.order'].sudo().search([('company_id','=',1),('name','=',order)])
                    beneficiary = com_in[0].bank.id
                    
                    or_ref = com_in.order_ref.name or com_in.name
                    pi_date = com_in.order_ref.pi_date or com_in.pi_date
                    po_no = style = ""
                    if com_in.po_no:
                        po_no = com_in.po_no
                    if com_in.style_ref:
                        style = com_in.style_ref
                    if pi_numbers:
                        if or_ref.replace('S','TZBD-Z') not in pi_numbers:
                            pi_numbers += "," + or_ref.replace('S','TZBD-Z') + " DT:" + pi_date.strftime('%d-%m-%Y')
                    else:
                        if or_ref.replace('S','TZBD-Z') not in pi_numbers:
                            pi_numbers += or_ref.replace('S','TZBD-Z') + " DT:" + pi_date.strftime('%d-%m-%Y')
                    if po_numbers:
                        if po_no not in po_numbers:
                            po_numbers += "," + po_no
                    else:
                        if po_no not in po_numbers:
                            po_numbers += po_no
                    if style_ref:
                        if style not in style_ref:
                            style_ref += "," + style
                    else:
                        if style not in style_ref:
                            style_ref += style

            
            else:
                if hs_code:
                    hs_code = '9607.11.00 AND 9606.22.00'
                else:
                    hs_code = '9606.22.00'
                m_invoice = mv.id
                order_list = [str(i) for i in sorted(mv.invoice_origin.split(','))]
                for order in order_list:
                    order = order.strip()
                    com_in = self.env['sale.order'].sudo().search([('company_id','=',3),('name','=',order)])
                    beneficiary = com_in[0].bank.id
                    or_ref = com_in.order_ref.name or com_in.name
                    pi_date = com_in.order_ref.pi_date or com_in.pi_date
                    po_no = style = ""
                    if com_in.po_no:
                        po_no = com_in.po_no
                    if com_in.style_ref:
                        style = com_in.style_ref
                    if pi_numbers:
                        pi_numbers += "," + or_ref.replace('S','TZBD-B') + " DT:" + pi_date.strftime('%d-%m-%Y')
                        po_numbers += "," + po_no
                        style_ref += "," + style
                    else:
                        pi_numbers += or_ref.replace('S','TZBD-B') + " DT:" + pi_date.strftime('%d-%m-%Y')
                        po_numbers += po_no
                        style_ref += style
                    
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
            'pi_numbers':pi_numbers,
            'po_numbers':po_numbers,
            'hs_code':hs_code,
            'beneficiary':beneficiary,
            'style_ref':style_ref,
            'state':moves[0].state,
        }
        return invoice_vals

    def _prepare_invoice_for_update(self,moves):
        z_invoice = m_invoice =  hs_code = beneficiary = None
        pi_numbers = po_numbers = style_ref =""
        for mv in moves:
            if mv.company_id.id == 1:
                hs_code = '9607.11.00'
                z_invoice = mv.id
                order_list = [str(i) for i in sorted(mv.invoice_origin.split(','))]
                i = 0
                for order in order_list:
                    order = order.strip()
                    com_in = self.env['sale.order'].sudo().search([('company_id','=',1),('name','=',order)])
                    beneficiary = com_in[0].bank.id
                    or_ref = com_in.order_ref.name or com_in.name
                    pi_date = com_in.order_ref.pi_date or com_in.pi_date
                    po_no = style = ""
                    if com_in.po_no:
                        po_no = com_in.po_no
                    if com_in.style_ref:
                        style = com_in.style_ref
                    if pi_numbers:
                        if or_ref.replace('S','TZBD-Z') not in pi_numbers:
                            pi_numbers += "," + or_ref.replace('S','TZBD-Z') + " DT:" + pi_date.strftime('%d-%m-%Y')
                    else:
                        if or_ref.replace('S','TZBD-Z') not in pi_numbers:
                            pi_numbers += or_ref.replace('S','TZBD-Z') + " DT:" + pi_date.strftime('%d-%m-%Y')
                    if po_numbers:
                        if po_no not in po_numbers:
                            po_numbers += "," + po_no
                    else:
                        if po_no not in po_numbers:
                            po_numbers += po_no
                    if style_ref:
                        if style not in style_ref:
                            style_ref += "," + style
                    else:
                        if style not in style_ref:
                            style_ref += style

            
            else:
                if hs_code:
                    hs_code = '9607.11.00 AND 9606.22.00'
                else:
                    hs_code = '9606.22.00'
                m_invoice = mv.id
                order_list = [str(i) for i in sorted(mv.invoice_origin.split(','))]
                for order in order_list:
                    order = order.strip()
                    com_in = self.env['sale.order'].sudo().search([('company_id','=',3),('name','=',order)])
                    beneficiary = com_in[0].bank.id
                    or_ref = com_in.order_ref.name or com_in.name
                    pi_date = com_in.order_ref.pi_date or com_in.pi_date
                    po_no = style = ""
                    if com_in.po_no:
                        po_no = com_in.po_no
                    if com_in.style_ref:
                        style = com_in.style_ref
                    if pi_numbers:
                        pi_numbers += "," + or_ref.replace('S','TZBD-B') + " DT:" + pi_date.strftime('%d-%m-%Y')
                        po_numbers += "," + po_no
                        style_ref += "," + style
                    else:
                        pi_numbers += or_ref.replace('S','TZBD-B') + " DT:" + pi_date.strftime('%d-%m-%Y')
                        po_numbers += po_no
                        style_ref += style
                    
        self.ensure_one()
        
        invoice_vals = {
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
            'pi_numbers':pi_numbers,
            'po_numbers':po_numbers,
            'hs_code':hs_code,
            'beneficiary':beneficiary,
            'style_ref':style_ref,
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
# insert into combine_invoice_line(invoice_id,parent_state,sequence,currency_id,product_uom_id,product_id,quantity,price_unit,discount,price_subtotal,price_total)
# values(50,'posted',100,2,1,118570,5,25.0,0,125.0,125.0);

    def _prepare_mould(self, qty,value):
        price = value/qty
        res = {
            'invoice_id':None,
            'sale_order_line':None,
            'account_move_line':None,
            'parent_state':'posted',
            'sequence':100,
            'currency_id':2,
            'product_uom_id':1,
            'product_id':118570,
            'product_uom_category_id':1,
            'quantity':qty,
            'price_unit':price,
            'discount':0,
            'price_subtotal':value,
            'price_total':value
            }
        return res