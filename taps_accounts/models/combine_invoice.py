# -*- coding: utf-8 -*-
import json
import datetime
import math
import operator as py_operator
import re
from num2words import num2words
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from werkzeug.urls import url_encode
from datetime import datetime


class CombineInvoice(models.Model):
    _name = "combine.invoice"
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Customer Invoice"
    _check_company_auto = False

    # ==== Business fields ====
    name = fields.Char(string='Number', copy=False, readonly=False, store=True, index=True, tracking=True)
    currency_id = fields.Many2one('res.currency', store=True, readonly=True, string='Currency')
    line_id = fields.One2many('combine.invoice.line', 'invoice_id', string='Customer Invoice Items', copy=True, readonly=True,)
    partner_id = fields.Many2one('res.partner', readonly=True ,string='Partner', states={'draft': [('readonly', False)]})
    # commercial_partner_id = fields.Many2one('res.partner', string='Commercial Entity', store=True, readonly=True,
    #     compute='_compute_commercial_partner_id', ondelete='restrict')
    # country_code = fields.Char(related='company_id.country_id.code', readonly=True)
    # user_id = fields.Many2one(string='User', related='invoice_user_id',
    #     help='Technical field used to fit the generic behavior in mail templates.')
    
    partner_bank_id = fields.Many2one('res.partner.bank', string='Recipient Bank',store=True, readonly=False)
    payment_reference = fields.Char(string='Payment Reference', store=True, readonly=False)
     
    invoice_date = fields.Date(string='Invoice/Bill Date', readonly=True, index=True, copy=False,)
    invoice_payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms',
        readonly=True)
    # /!\ invoice_line_ids is just a subset of line_ids.
    # invoice_line_ids = fields.One2many('account.move.line', 'move_id', string='Invoice lines',
    #     copy=False, readonly=True,
    #     domain=[('exclude_from_invoice_tab', '=', False)],
    #     states={'draft': [('readonly', False)]})
    invoice_incoterm_id = fields.Many2one('account.incoterms', string='Incoterm')
    beneficiary = fields.Many2one('res.bank', string='Beneficiary',readonly=False, store=True)
    issued_by = fields.Many2one('res.bank', string='Issued By',readonly=False, store=True)
    issued_address = fields.Char(string='Bank Address', store=True, readonly=False)
    z_invoice = fields.Many2one('account.move', string='Zipper Invoice',readonly=False, store=True)
    m_invoice = fields.Many2one('account.move', string='Metal Trims Invoice',readonly=False, store=True)
    pi_numbers = fields.Char(string='PI No.', store=True, readonly=False)
    po_numbers = fields.Char(string='PO No.', store=True, readonly=False)
    style_ref = fields.Char(string='Style Ref.', store=True, readonly=False)
    hs_code = fields.Char(string='HS Code', store=True, readonly=False)
    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled'),
        ], string='Status', required=True, readonly=True, copy=False, tracking=True,
        default='draft')
    applicant_tin = fields.Char(string="APPLICANT'S TIN", store=True, readonly=False)
    bin_vat_reg = fields.Char(string='BIN/VAT REG.NO', store=True, readonly=False)
    bond_licence = fields.Char(string='BOND LICENSE NO', store=True, readonly=False)
    tin_no = fields.Char(string='TIN NO', store=True, readonly=False)
    bank_bin = fields.Char(string='BANK BIN NO', store=True, readonly=False)
    lc_no = fields.Char(string='LC', store=True, readonly=False)
    lc_date = fields.Date(string='LC Date', store=True, readonly=False)
    master_lc = fields.Char(string='Export LC NO', store=True, readonly=False)
    master_date = fields.Date(string='Export LC Date', store=True, readonly=False)
    exp_no = fields.Char(string='Document/Export NO', store=True, readonly=False)
    exp_date = fields.Date(string='Document/Export Date', store=True, readonly=False)
    numberof_carton = fields.Float('No. of Ctn', default=0.0, store=True)
    gross_weight = fields.Float('Gross Weight', default=0.0, store=True)
    net_weight = fields.Float('Net Weight', default=0.0, store=True)
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', tracking=4)

    @api.depends('line_id.price_total')
    def _amount_all(self):
        for order in self:
            amount_total = 0.0
            for line in order.line_id:
                amount_total += line.price_subtotal
            order.update({
                'amount_total': amount_total,
            })
    
    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            # seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_order']))
            _name = 'New'
            _name = self.env['ir.sequence'].next_by_code('combine.invoice', sequence_date=seq_date) or _('New')
            match = re.search(r'(\d{4})', _name)
            year = match.group(1)
            n_year = str(int(year)+1)
            n_year = n_year[-2:]
            _name = _name.replace(str(year),str(year)+'-'+n_year)
            # raise UserError((_name))
            vals['name'] = _name
        
        result = super(CombineInvoice, self).create(vals)
        return result
    
    

class CombineInvoiceLine(models.Model):
    _name = "combine.invoice.line"
    _description = "Customer Invoice Items"
    _check_company_auto = False

    # ==== Business fields ====
    invoice_id = fields.Many2one('combine.invoice', string='Customer Invoice Items',
        index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    # move_id = fields.Many2one('account.move', string='Customer Invoice Items', index=True, required=True, readonly=True, auto_join=True, ondelete="cascade")
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    account_move_line = fields.Many2one('account.move.line', string='Move Line', store=True, readonly=True)
    parent_state = fields.Selection(related='invoice_id.state', store=True, readonly=True)
    sequence = fields.Integer(default=10)
    currency_id = fields.Many2one('res.currency', string='Currency')
    product_uom_id = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_id = fields.Many2one('product.product', related='account_move_line.product_id', string='Product Id', ondelete='restrict')
    product_uom_category_id = fields.Many2one('uom.category', related='product_id.uom_id.category_id')
    # product_id = fields.Many2one('product.product', related='sale_order_line.product_id', string='Product Id',ondelete='restrict', check_company=True)
    product_template_id = fields.Many2one(
        'product.template', string='Product',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Char(string='Item', related='product_template_id.fg_categ_type.name', store=True)
    
    finish = fields.Text(string='Finish', related='sale_order_line.finish', store=True, readonly=True)
    shade = fields.Text(string='Shade', related='sale_order_line.shade', store=True, readonly=True)
    sizcommon = fields.Text(string='Size', store=True, readonly=False, compute='compute_size')
    quantity = fields.Float(string='Quantity', digits='Product Unit of Measure')
    price_unit = fields.Float(string='Unit Price', digits='Product Price')
    discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal', store=True, readonly=True,
        currency_field='currency_id')
    price_total = fields.Monetary(string='Total', store=True, readonly=True,
        currency_field='currency_id')

    
    @api.depends('sale_order_line.sizein', 'sale_order_line.sizecm', 'sale_order_line.sizemm')
    def compute_size(self):
        for s in self:
            if s.sale_order_line.sizein !=False and s.sale_order_line.sizein != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizein) + ' In' 
            elif s.sale_order_line.sizecm !=False and s.sale_order_line.sizecm != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizecm) + ' Cm'
            elif s.sale_order_line.sizemm !=False and s.sale_order_line.sizemm != 'N/A':
                s.sizcommon = str(s.sale_order_line.sizemm) + ' Mm'



class CombineInvoiceReport(models.AbstractModel):
    _name = 'report.taps_accounts.report_customer_invoice'
    _description = 'Customer Invoice'     

    def _get_report_values(self, docids, data=None):
        # raise UserError((docids))
        docs = self.env['combine.invoice'].sudo().browse(docids)
        line_data = self.env['combine.invoice.line'].sudo().search([('invoice_id','in',docids)])
        z_items = line_data.filtered(lambda x: x.product_id.product_tmpl_id.company_id.id == 1)
        m_items = line_data.filtered(lambda x: x.product_id.product_tmpl_id.company_id.id == 3)
        z_total_qty = z_total_value = m_total_qty = m_total_value = m_total_pcs = total_value = 0
        total_qty = sum(line_data.mapped('quantity'))
        total_value = sum(line_data.mapped('price_total'))
        if z_items:
            z_total = sum(z_items.mapped('quantity'))
            z_total_value = sum(z_items.mapped('price_total'))
        if m_items:
            m_total = sum(m_items.mapped('quantity'))
            m_total_pcs = m_total*144
            m_total_value = sum(m_items.mapped('price_total'))
        report_data = []
        if line_data:
            companies = line_data.mapped('product_template_id.company_id')
            for com in companies:
                com_line_data = line_data.filtered(lambda x: x.product_template_id.company_id.id == com.id)
                
                all_item = com_line_data.mapped('product_template_id')
                # raise UserError((all_item.id))
                for item in all_item:
                    single_item = com_line_data.filtered(lambda x: x.product_template_id.id == item.id)
                    all_finish = single_item.mapped('finish')
                    all_finish = list(set(all_finish))
                    for finish in all_finish:
                        single_finish = single_item.filtered(lambda x: x.finish == finish)
                        all_shade = single_finish.mapped('shade')
                        all_shade = list(set(all_shade))
                        for shade in all_shade:
                            single_shade = single_finish.filtered(lambda x: x.shade == shade)
                            all_size = single_shade.mapped('sizcommon')
                            all_size = list(set(all_size))
                            for size in all_size:
                                single_size = single_finish.filtered(lambda x: x.sizcommon == size)
                                qty = sum(single_size.mapped('quantity'))
                                value = sum(single_size.mapped('price_subtotal'))
                                price = value/qty
                                
                                order_data = []
                                order_data = [
                                    item.name,
                                    finish,
                                    shade,
                                    size,
                                    qty,
                                    round(price,4),
                                    round(value,4),
                                    ]
                                report_data.append(order_data)
                order_data = []
                if com.id == 1:
                    order_data = ['Sub Total (zipper)','','','',z_total,'',round(z_total_value,2),]
                if com.id == 3:
                    order_data = ['Sub Total (button)','','','',m_total_pcs,'',round(m_total_value,2),]
                # raise UserError((com.id,order_data))
                report_data.append(order_data)

        sales_person = None
        sales_person = docs.line_id[0].sale_order_line[0].order_id.user_id.name
        amount_in_word = self._amount_in_words(total_value)    
        
        common_data = [sales_person,z_total_qty,z_total_value,m_total_qty,m_total_value,m_total_pcs,total_qty,total_value,amount_in_word]
        # raise UserError((report_data))
        return {
            'docs': docs,
            'datas': report_data,
            'common_data':common_data,
            # 'company': com_id,
            'doc_model': 'combine.invoice',
            }
            

    def _amount_in_words(self,amount):
        total = 0.0
        total = format(amount, ".2f")
        text = ''
        entire_num = int((str(total).split('.'))[0])
        decimal_num = int((str(total).split('.'))[1])
        text+=num2words(entire_num, lang='en_IN')
        if entire_num == 1:
            text+=' dollar '
        else:
            text+=' dollars '
        if decimal_num > 0:
            text+=num2words(decimal_num, lang='en_IN')
            if decimal_num == 1:
                text+=' cent '
            else:
                text+=' cents '
        amount_in_word = text.upper()
        return amount_in_word

