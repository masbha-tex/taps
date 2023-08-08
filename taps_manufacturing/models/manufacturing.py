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

SIZE_BACK_ORDER_NUMERING = 3


class SaleOrder(models.Model):
    _name = "manufacturing.order"
    #_inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = "Manufacturing Order"
    #_order = 'date_order desc, id desc'
    _check_company_auto = True

    #sequence = fields.Integer(string='Sequence')
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', readonly=True, store=True)
    oa_id = fields.Many2one('sale.order', related='sale_order_line.order_id', string='OA', readonly=True, store=True)
    company_id = fields.Many2one('res.company', related='oa_id.company_id', string='Company', readonly=True, store=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    #buyer_name = fields.Many2one('sale.buyer', related='oa_id.buyer_name.id', string='Buyer', readonly=True)
    payment_term = fields.Many2one('account.payment.term', related='oa_id.payment_term_id', string='Payment Term', readonly=True)
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    validity_date = fields.Date(string='Expiration', related='oa_id.validity_date', readonly=True)
    
    lead_time = fields.Integer(string='Lead Time', compute='get_leadtime', readonly=True)
    
    product_id = fields.Many2one(
        'product.product', related='sale_order_line.product_id', string='Product',ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Selection(related='product_template_id.fg_categ_type')
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_template_id.uom_id')
    product_uom_qty = fields.Float(string='Quantity', related='sale_order_line.product_uom_qty', digits='Product Unit of Measure', readonly=True)
    done_qty = fields.Float(string='Done Quantity', digits='Product Unit of Measure', readonly=False)
    balance_qty = fields.Float(string='Balance Quantity', compute='_balance_qty', digits='Product Unit of Measure', readonly=True)
    
    topbottom = fields.Char(string='Top/Bottom', store=True, readonly=True)
    slidercodesfg = fields.Char(string='Slider Code (SFG)', store=True, readonly=True)
    finish = fields.Char(string='Finish', store=True, readonly=True)
    shade = fields.Char(string='Shade', store=True, readonly=True)
    sizein = fields.Char(string='Size (Inch)', store=True, readonly=True)
    sizecm = fields.Char(string='Size (CM)', store=True, readonly=True)
    sizemm = fields.Char(string='Size (MM)', store=True, readonly=True)
    
    dyedtape = fields.Char(string='Dyed Tape', store=True, readonly=True)
    ptopfinish = fields.Char(string='Plated Top Finish', store=True, readonly=True)
    
    numberoftop = fields.Char(string='Number of Top', store=True, readonly=True)
    
    pbotomfinish = fields.Char(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Char(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Char(string='Dipping Finish', store=True)
    gap = fields.Char(string='Gap', store=True)
    
    logo = fields.Text(string='Logo', store=True)
    logoref = fields.Text(string='Logo Ref', store=True)
    logo_type = fields.Text(string='Logo Type', store=True)
    style = fields.Text(string='Style', store=True)
    gmt = fields.Text(string='Gmt', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    b_part = fields.Text(string='B Part', store=True)
    c_part = fields.Text(string='C Part', store=True)
    d_part = fields.Text(string='D Part', store=True)
    finish_ref = fields.Text(string='Finish Ref', store=True)
    product_code = fields.Text(string='Product Code', store=True)
    shape = fields.Text(string='Shape', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    back_part = fields.Text(string='Back Part', store=True)
    
    tape_con = fields.Float('Tape Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    slider_con = fields.Float('Slider Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    topwire_con = fields.Float('Topwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    botomwire_con = fields.Float('Botomwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    tbwire_con = fields.Float('TBwire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    wire_con = fields.Float('Wire Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    pinbox_con = fields.Float('Pinbox Consumption', compute='_get_line_value', readonly=True, digits='Unit Price')
    shadewise_tape = fields.Float('Shadwise Tape', compute='_get_line_value', readonly=True, digits='Unit Price')

    dyeing_plan = fields.Datetime(string='Dyeing Plan Start', readonly=False)
    dyeing_plan_end = fields.Datetime(string='Dyeing Plan End', readonly=False)
    dyeing_plan_qty = fields.Float(string='Dyeing Plan Qty', readonly=False)
    dy_rec_plan_qty = fields.Float(string='Dyeing Replan Qty', readonly=False, default=0.0)
    dyeing_plan_due = fields.Float(string='Dyeing Plan Due', readonly=False, compute='_dy_plane_due')
    dyeing_output = fields.Float(string='Dyeing Output', readonly=False)
    dyeing_qc_pass = fields.Float(string='Dyeing QC Pass', readonly=False)

    plating_plan = fields.Datetime(string='Plating Plan Start', readonly=False)
    plating_plan_end = fields.Datetime(string='Plating Plan End', readonly=False)
    plating_plan_qty = fields.Float(string='Plating Plan Qty', readonly=False)
    pl_rec_plan_qty = fields.Float(string='Plating Replan Qty', readonly=False, default=0.0)
    plating_output = fields.Float(string='Plating Output', readonly=False)
    plating_qc_pass = fields.Float(string='Plating QC Pass', readonly=False)

    sli_asmbl_plan = fields.Datetime(string='Slider Asmbl Plan Start', readonly=False)
    sli_asmbl_plan_end = fields.Datetime(string='Slider Asmbl Plan End', readonly=False)
    sli_asmbl_plan_qty = fields.Float(string='Slider Asmbl Plan Qty', readonly=False)

    painting_done = fields.Float(string='painting Output', readonly=False)
    
    chain_making_done = fields.Float(string='CM Output', readonly=False)
    diping_done = fields.Float(string='Dipping Output', readonly=False)
    assembly_done = fields.Float(string='Assembly Output', readonly=False)
    packing_done = fields.Float(string='Packing Output', readonly=False)



    def get_leadtime(self):
        for s in self:
            s.lead_time = (datetime.now() - s.date_order).days
    
    def _balance_qty(self):
        for s in self:
            s.balance_qty = s.product_uom_qty - s.done_qty
    
    def _dy_plane_due(self):
        for s in self:
            s.dyeing_plan_due = s.tape_con - s.dyeing_plan_qty
    
    def _get_line_value(self):
        for s in self:
            s.tape_con = s.sale_order_line.tape_con
            s.slider_con = s.sale_order_line.slider_con
            s.topwire_con = s.sale_order_line.topwire_con
            s.botomwire_con = s.sale_order_line.botomwire_con
            s.tbwire_con = s.sale_order_line.tbwire_con
            s.wire_con = s.sale_order_line.wire_con
            s.pinbox_con = s.sale_order_line.pinbox_con
            s.shadewise_tape = s.sale_order_line.shadewise_tape
            
    #         s.sizecm = s.sale_order_line.sizecm
    #         s.sizemm = s.sale_order_line.sizemm
    #         s.dyedtape = s.sale_order_line.dyedtape
    #         s.ptopfinish = s.sale_order_line.ptopfinish
    #         s.numberoftop = s.sale_order_line.numberoftop
    #         s.pbotomfinish = s.sale_order_line.pbotomfinish
    #         s.ppinboxfinish = s.sale_order_line.ppinboxfinish
    #         s.dippingfinish = s.sale_order_line.dippingfinish
    #         s.gap = s.sale_order_line.gap
    #         s.logo = s.sale_order_line.logo
    #         s.logoref = s.sale_order_line.logoref
    #         s.logo_type = s.sale_order_line.logo_type
    #         s.style = s.sale_order_line.style
    #         s.gmt = s.sale_order_line.gmt
    #         s.shapefin = s.sale_order_line.shapefin
    #         s.bcdpart = s.sale_order_line.bcdpart
    #         s.b_part = s.sale_order_line.b_part
    #         s.c_part = s.sale_order_line.c_part
    #         s.d_part = s.sale_order_line.d_part
    #         s.finish_ref = s.sale_order_line.finish_ref
    #         s.product_code = s.sale_order_line.product_code
    #         s.shape = s.sale_order_line.shape
    #         s.nailmat = s.sale_order_line.nailmat
    #         s.nailcap = s.sale_order_line.nailcap
    #         s.fnamebcd = s.sale_order_line.fnamebcd
    #         s.nu1washer = s.sale_order_line.nu1washer
    #         s.nu2washer = s.sale_order_line.nu2washer
    #         s.back_part = s.sale_order_line.back_part
        

    def button_plan(self):
        self._check_company()
        # if self.state in ("done", "to_close", "cancel"):
        #     raise UserError(
        #         _(
        #             "Cannot split a manufacturing order that is in '%s' state.",
        #             self._fields["state"].convert_to_export(self.state, self),
        #         )
        #     )
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_plan")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        #action["context"] = {"default_item_qty": 20,"default_material_qty": 12}
        return action

# mo_ids,self.plan_for,self.plan_start,self.plan_end,self.plan_qty
    def set_plan(self,mo_ids,plan_for,plan_start,plan_end,plan_qty,machine_line):
        #raise UserError((mo_ids,plan_for,plan_start,plan_end,plan_qty))
        production = self.env["manufacturing.order"].browse(mo_ids)
# dyeing_plan,dyeing_plan_end,dyeing_plan_qty,dyeing_output,dyeing_qc_pass
# plating_plan,plating_plan_end,plating_plan_qty,plating_output,plating_qc_pass
        m_qty = 0.00
        rest_pl_q = plan_qty
        p_len = len(production)
        dist_qty = plan_qty / p_len
        
        addition = 0.00
        for p in production:
            if plan_for == 'dyeing':
                if p.tape_con <= rest_pl_q:
                    m_qty = p.tape_con
                    rest_pl_q = rest_pl_q - p.tape_con
                else:
                    m_qty = rest_pl_q
                    rest_pl_q = 0.00
                re_pqty = m_qty 
                m_qty += p.dyeing_plan_qty
                p.update({'dyeing_plan':plan_start,'dyeing_plan_end':plan_end,'dyeing_plan_qty':m_qty,
                         'dy_rec_plan_qty':re_pqty})

            # if plan_for == 'dyeing':
            #     if p.tape_con < dist_qty + addition:
            #         m_qty = p.tape_con
            #         addition = (dist_qty + addition) - p.tape_con
            #     else:
            #         m_qty = dist_qty + addition
            #         addition = 0.00
            #     re_pqty = m_qty 
            #     m_qty += p.dyeing_plan_qty
            #     p.write({'dyeing_plan':plan_start,'dyeing_plan_end':plan_end,'dyeing_plan_qty':m_qty,
            #              'dy_rec_plan_qty':re_pqty})
                
            elif plan_for == 'sliderplating':
                if p.tape_con < dist_qty + addition:
                    m_qty = p.slider_con
                    addition = (dist_qty + addition) - p.slider_con
                else:
                    m_qty = dist_qty + addition
                    addition = 0
                m_qty += p.plating_plan_qty
                p.update({'plating_plan':plan_start,'plating_plan_end':plan_end,'plating_plan_qty':m_qty})
            elif plan_for == 'topplating':
                m_qty += p.topwire_con
            elif plan_for == 'bottomplating':
                m_qty += p.botomwire_con
            elif plan_for == 'sliassembly':
                m_qty += p.slider_con
    
    
        if plan_for == 'dyeing':
            query = """ select oa_id,shade,'' as finish,'' as slidercodesfg,sum(dy_rec_plan_qty) as qty from manufacturing_order where id in %s and 1=%s group by oa_id,shade """
        if plan_for == 'sliderplating':
            query = """ select oa_id,'' as shade, finish,slidercodesfg,sum(pl_rec_plan_qty) as qty from manufacturing_order where id in %s and 1=%s group by oa_id,finish,slidercodesfg """
            
        cr = self._cr
        cursor = self.env.cr
        cr.execute(query,[tuple(mo_ids),1])
        plan = cursor.fetchall()
        if machine_line:
            for m in machine_line:
                for p in plan:
                    qty = 0.0
                    if plan_for == 'dyeing':
                        p_q = production.filtered(lambda sol: sol.oa_id.id == p[0] and sol.shade == p[1])
                        qty = sum(p_q.mapped('dy_rec_plan_qty'))
                    if plan_for == 'sliderplating':
                        p_q = production.filtered(lambda sol: sol.oa_id.id == p[0] and sol.finish == p[2] and sol.slidercodesfg == p[3])
                        qty = sum(p_q.mapped('pl_rec_plan_qty'))

                    #raise UserError((p_q[0].dy_rec_plan_qty))
                    
                    #and sol.finish == p[2]
                    
                    mrp_ = self.env['operation.details'].create({'mrp_lines':None,
                                                                 'sale_lines':None,
                                                                 'mrp_line':None,
                                                                 'sale_order_line':None,
                                                                 'oa_id':p[0],
                                                                 'action_date':plan_start,
                                                                 'shade':p[1],
                                                                 'finish':p[2],
                                                                 'slidercodesfg':p[3],
                                                                 'operation_of':'plan',
                                                                 'operation_by':'planning',
                                                                 'based_on':m.machine_no,
                                                                 'qty':qty,
                                                                 'done_qty':0
                                                                 })

    def button_requisition(self):
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_requisition")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        return action
    
    def button_createlot(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

    def button_output(self):
        self.ensure_one()
        self._check_company()
        if self.state in ("done", "to_close", "cancel"):
            raise UserError(
                _(
                    "Cannot split a manufacturing order that is in '%s' state.",
                    self._fields["state"].convert_to_export(self.state, self),
                )
            )
        action = self.env["ir.actions.actions"]._for_xml_id("mrp.action_split_mrp")
        action["context"] = {"default_mo_id": self.id,"default_product_id": self.product_id}
        return action

