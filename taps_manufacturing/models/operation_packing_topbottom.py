import json
import datetime
import math
import operator as py_operator
import re

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

class OperationPackingTopbottom(models.Model):
    _name = "operation.packing.topbottom"
    _description = "Top & Bottom Packing"
    _check_company_auto = True
    
    name = fields.Char(string='Code', store=True)
    sale_order_option = fields.Many2one('sale.order.option',string='Sale Order Option', readonly=True, store=True, check_company=True)
    sale_order_line = fields.Many2one('sale.order.line', related='sale_order_option.line_id', string='Sale Order Line', readonly=True, store=True, check_company=True)
    
    oa_id = fields.Many2one('sale.order', related='sale_order_option.order_id', string='OA', readonly=True, store=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]", check_company=True)
    
    company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True, store=True)

    product_id = fields.Many2one('product.product', related='sale_order_option.product_id',  check_company=True, string='Product Id')
                
    product_template_id = fields.Many2one('product.template', string='Product', related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)], store=True)
    
    fg_categ_type = fields.Char(string='Item', related='product_template_id.fg_categ_type.name', store=True)
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_template_id.uom_id')
    
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    action_date = fields.Datetime(string='Action Date', readonly=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    buyer_name = fields.Char(string='Buyer', readonly=True)
    
    slidercodesfg = fields.Text(string='Slider Code', related='sale_order_line.slidercodesfg', store=True, readonly=True)
    finish = fields.Text(string='Finish', related='sale_order_line.finish', store=True, readonly=True)
    shade = fields.Text(string='Shade', related='sale_order_line.shade', store=True, readonly=True)
    shade_ref = fields.Text(string='Shade Ref.', related='sale_order_line.shade_ref', store=True, readonly=True)
  
    sizein = fields.Text(string='Size (Inch)', related='sale_order_line.sizein', store=True, readonly=True)
    sizecm = fields.Text(string='Size (CM)', related='sale_order_line.sizecm', store=True, readonly=True)
    sizemm = fields.Text(string='Size (MM)', related='sale_order_line.sizemm', store=True, readonly=True)
    sizcommon = fields.Text(string='Size', store=True, readonly=True, compute='compute_size')

    @api.depends('sizein', 'sizecm', 'sizemm')
    def compute_size(self):
        for s in self:
            if s.sizein !=False and s.sizein != 'N/A':
                s.sizcommon = str(s.sizein) + ' In' 
            elif s.sizecm !=False and s.sizecm != 'N/A':
                s.sizcommon = str(s.sizecm) + ' Cm'
            elif s.sizemm !=False and s.sizemm != 'N/A':
                s.sizcommon = str(s.sizemm) + ' Mm'
    
    top = fields.Text(string='Top', related='sale_order_line.ptopfinish', store=True, readonly=True)
    bottom = fields.Text(string='Bottom', related='sale_order_line.pbotomfinish', store=True)
    pinbox = fields.Text(string='Pin-Box', related='sale_order_line.ppinboxfinish', store=True)
    logo = fields.Text(string='Logo', related='sale_order_line.logo', store=True, readonly=True)
    logoref = fields.Text(string='Logo Ref', related='sale_order_line.logoref', store=True, readonly=True)
    logo_type = fields.Text(string='Logo Type', related='sale_order_line.logo_type', store=True, readonly=True)
    style = fields.Text(string='Style', related='sale_order_line.style', store=True, readonly=True)
    gmt = fields.Text(string='Gmt', related='sale_order_line.gmt', store=True, readonly=True)
    shapefin = fields.Text(string='Shape Finish', related='sale_order_line.shapefin', store=True, readonly=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', related='sale_order_line.bcdpart', store=True, readonly=True)
    b_part = fields.Text(string='B Part', related='sale_order_line.b_part', store=True, readonly=True)
    c_part = fields.Text(string='C Part', related='sale_order_line.c_part', store=True, readonly=True)
    d_part = fields.Text(string='D Part', related='sale_order_line.d_part', store=True, readonly=True)
    finish_ref = fields.Text(string='Finish Ref', related='sale_order_line.finish_ref', store=True, readonly=True)
    product_code = fields.Text(string='Product Code', related='sale_order_line.product_code', store=True, readonly=True)
    shape = fields.Text(string='Shape', related='sale_order_line.shape', store=True, readonly=True)
    back_part = fields.Text(string='Back Part', related='sale_order_line.back_part', store=True, readonly=True)
    work_center = fields.Many2one('mrp.workcenter', string='Assign To', store=True, readonly=True, help="Assign to")
    
    @api.depends('qty', 'done_qty', 'actual_qty')
    def get_ac_balance(self):
        for s in self:
            if s.actual_qty>0:
                s.ac_balance_qty = round((s.actual_qty - s.done_qty),2)
                s.balance_qty = round((s.actual_qty - s.done_qty),2)
            # if s.qty>0:
            #     s.balance_qty = round((s.qty - s.done_qty),2)

    actual_qty = fields.Float(string='OA Qty', related='sale_order_option.quantity', readonly=True, store=True, group_operator="sum")
    # actual_qty = fields.Float(string='OA Qty', readonly=True, store=True, group_operator="sum")
    ac_balance_qty = fields.Float(string='OA Balance', readonly=False, store=True, compute='get_ac_balance', group_operator="sum")
    qty = fields.Float(string='Qty', readonly=False)
    # price_unit = fields.Float('Unit Price', digits='Product Price', default=0.0, store=True)
    price_unit = fields.Float('Unit Price', related='sale_order_option.price_unit', digits='Product Price', default=0.0, readonly=True, store=True)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=False, store=True, compute='get_ac_balance', group_operator="sum")
    uotput_qty = fields.Float(string='Output', default=0.0, readonly=False)
    revision_no = fields.Char(string='Revision No', store=True)
    closing_date = fields.Datetime(string='Closing Date', readonly=False)
    return_qty = fields.Float(string='Return Qty', default=0.0, readonly=False)
    
    sale_line_of_top = fields.Integer(string='Sale Line of Top', store=True, readonly=True)
    
    state = fields.Selection([
        ('waiting', 'Waiting'),
        ('partial', 'Partial'),
        ('done', 'Done'),
        ('hold', 'Hold'),
        ('cancel', 'Cancelled'),
        ('closed', 'Closed')],
        string='State')

    def _ids2str(self,field_name):
        field_data = getattr(self, field_name)
        if field_name == "ids":
            return ','.join([str(i) for i in sorted(field_data)])
        else:
            return ','.join([str(i.id) for i in sorted(field_data)])

    def button_change_packing_date(self):
        # self.ensure_one()
        self._check_company()
        for record in self:
            if record.next_operation != 'FG Packing':
                raise UserError(('This is not for you'))
        unique_dates = set(record.action_date.date() for record in self)
        if len(unique_dates) > 1:
            raise UserError(('You can change date only for one date'))
            
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.change_production_date")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action
        
    def button_group_output(self):
        for r in self:
            if r.next_operation in ('Chain Making','Gapping'):
                raise UserError(('This is not for you'))
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_group_output")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action

    def button_return(self):
        self.ensure_one()
        self._check_company()
        if self.next_operation != 'FG Packing':
            raise UserError(('This is not for you'))    
        
    def button_output(self):
        self.ensure_one()
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_output")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action

    @api.model
    def create(self, vals):
        if 'company_id' in vals:
            self = self.with_company(vals['company_id'])
        seq_date = None
        seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(datetime.now()))

        ref = self.env['ir.sequence'].next_by_code('mrp.lot', sequence_date=seq_date)
        vals['name'] = ref
        # raise UserError((ref))    
        vals['state'] = 'waiting'
        result = super(OperationPackingTopbottom, self).create(vals)
        return result                

    # @api.model
    def write(self, vals):
        if 'done_qty' in vals:
            if self.state not in('done','closed'):
                if round(self.actual_qty,2) <= round(vals.get('done_qty'),2):
                    vals['state'] = 'done'
                elif vals.get('done_qty') == 0:
                    vals['state'] = 'waiting'
                else:
                    vals['state'] = 'partial'
        result = super(OperationPackingTopbottom, self).write(vals)
        return result                

    def set_group_output(self,mo_ids,qty,planned_qty):
        operation = self.env["operation.packing.topbottom"].browse(mo_ids)
        qty_ = round((qty/len(operation)),2)
        if operation[0].next_operation == 'Dyeing Qc':
            rest_qty = qty
            while rest_qty > 0:
                for op in operation:
                    o_qty = op.done_qty + rest_qty
                    if op.ac_balance_qty >= o_qty:
                        op.write({'uotput_qty': rest_qty})
                        op._output()
                        rest_qty = 0
                    else:
                        if op.ac_balance_qty > op.done_qty:
                            o_qty = op.ac_balance_qty - op.done_qty
                            if o_qty > 0:
                                op.write({'uotput_qty': o_qty})
                                rest_qty = rest_qty - o_qty
                                op._output()
                            else:
                                rest_qty = 0
        else:
            for op in operation:
                if planned_qty == qty:
                    qty_ = op.balance_qty
                op.write({'uotput_qty':qty_})
                op._output()

    @api.onchange('uotput_qty')
    def _output(self):
        for out in self:
            pack_qty = 0
            fraction_pc_of_pack = 0
            pr_pac_qty = 0
            done_qty = out.done_qty + out.uotput_qty
            if (round(out.balance_qty,0) < round(out.uotput_qty,0)):
                raise UserError(('You can not produce more then balance'))
            if (out.state not in ('partial','waiting')):
                raise UserError(('You can not update this data because of state is done/closed'))
                
            s = out.write({'done_qty':done_qty})

            mrp_oa_data = self.env["manufacturing.order"].search([('oa_id','=',out.oa_id.id)])
            packing_balance = self.env["operation.packing"].search([('oa_id','=',out.oa_id.id),('balance_qty','>',0)])
            top_balance = self.env["operation.packing.topbottom"].search([('oa_id','=',out.oa_id.id),('balance_qty','>',0)])
            top_sum = 0
            if top_balance:
                top_sum = sum(top_balance.mapped('balance_qty'))
                top_sum -= out.uotput_qty
                
            if (not packing_balance) and (top_sum == 0):
                mrp_all_oa = mrp_oa_data.update({'oa_total_balance':0,'closing_date':datetime.now(),'state':'closed'})
                sl_closed = self.env["sale.order"].browse(out.oa_id.id)
                _slclosed = sl_closed.write({'closing_date':datetime.now().date()})

            
            move_line = None
            pr_pac_qty = 0
            pack_qty = 0#out.uotput_qty
            fraction_pc_of_pack = 0

            next = None
            w_center = None
            operation_of = 'output'
            can_create = True
            next = 'FG Packing'
            if can_create:
                ope = self.env['operation.details'].create({'name':out.name,
                                                        'sale_lines':out.sale_order_line.id,
                                                        'sale_order_line':out.sale_order_line.id,
                                                        'parent_id':out.id,
                                                        'oa_id':out.oa_id.id,
                                                        'buyer_name':out.buyer_name,
                                                        'product_id':out.product_id.id,
                                                        'product_template_id':out.product_template_id.id,
                                                        'action_date':datetime.now(),
                                                        'shade':out.shade,
                                                        'shade_ref':out.shade_ref,
                                                        'finish':out.finish,
                                                        'logo':out.logo,
                                                        'logoref':out.logoref,
                                                        'logo_type':out.logo_type,
                                                        'style':out.style,
                                                        'gmt':out.gmt,
                                                        'shapefin':out.shapefin,
                                                        'b_part':out.b_part,
                                                        'c_part':out.c_part,
                                                        'd_part':out.d_part,
                                                        'finish_ref':out.finish_ref,
                                                        'product_code':out.product_code,
                                                        'shape':out.shape,
                                                        'back_part':out.back_part,
                                                        'sizein':out.sizein,
                                                        'sizecm':out.sizecm,
                                                        'sizemm':out.sizemm,
                                                        'slidercodesfg':out.slidercodesfg,
                                                        'top':out.top,
                                                        'bottom':out.bottom,
                                                        'pinbox':out.pinbox,
                                                        'operation_of':operation_of,
                                                        'work_center':w_center,
                                                        'operation_by':'Packing',
                                                        'based_on':'Lot Code',
                                                        'next_operation':next,
                                                        'actual_qty':out.actual_qty,
                                                        'qty':out.uotput_qty,
                                                        'pack_qty':pack_qty,
                                                        'fr_pcs_pack':fraction_pc_of_pack,
                                                        'capacity':pr_pac_qty,
                                                        'move_line':move_line,
                                                        'price_unit':out.price_unit,
                                                        })
            out.uotput_qty = 0



