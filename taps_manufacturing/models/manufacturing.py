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
    
    topbottom = fields.Text(string='Top/Bottom', store=True, readonly=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True, readonly=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    sizemm = fields.Text(string='Size (MM)', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', store=True)
    
    numberoftop = fields.Text(string='Number of Top', store=True)
    
    pbotomfinish = fields.Text(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', store=True)
    gap = fields.Text(string='Gap', store=True)
    
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
    dyeing_plan_due = fields.Float(string='Dyeing Plan Due', readonly=False, compute='_dy_plane_due')
    dyeing_output = fields.Float(string='Dyeing Output', readonly=False)
    dyeing_qc_pass = fields.Float(string='Dyeing QC Pass', readonly=False)

    plating_plan = fields.Datetime(string='Plating Plan Start', readonly=False)
    plating_plan_end = fields.Datetime(string='Plating Plan End', readonly=False)
    plating_plan_qty = fields.Float(string='Plating Plan Qty', readonly=False)
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
    def set_plan(self,mo_ids,plan_for,plan_start,plan_end,plan_qty):
        production = self.env["manufacturing.order"].browse(mo_ids)
# dyeing_plan,dyeing_plan_end,dyeing_plan_qty,dyeing_output,dyeing_qc_pass
# plating_plan,plating_plan_end,plating_plan_qty,plating_output,plating_qc_pass
        m_qty = 0
        rest_pl_q = plan_qty
        p_len = len(production)
        dist_qty = plan_qty / p_len
        
        addition = 0
        for p in production:
            if plan_for == 'dyeing':
                if self.tape_con < dist_qty + addition:
                    m_qty = self.tape_con
                    addition = (dist_qty + addition) - self.tape_con
                else:
                    m_qty = dist_qty + addition
                    addition = 0
                m_qty += p.dyeing_plan_qty
                p.write({'dyeing_plan':plan_start,'dyeing_plan_end':plan_end,'dyeing_plan_qty':m_qty})
                
            elif plan_for == 'sliderplating':
                if self.tape_con < dist_qty + addition:
                    m_qty = self.slider_con
                    addition = (dist_qty + addition) - self.slider_con
                else:
                    m_qty = dist_qty + addition
                    addition = 0
                m_qty += p.plating_plan_qty
                p.write({'plating_plan':plan_start,'plating_plan_end':plan_end,'plating_plan_qty':m_qty})
            elif plan_for == 'topplating':
                m_qty += self.topwire_con
            elif plan_for == 'bottomplating':
                m_qty += self.botomwire_con
            elif plan_for == 'sliassembly':
                m_qty += self.slider_con

            
        # spl_qty = sum(split_line.mapped('product_qty'))
        # mrp_qty = production.product_qty
        # bal_qty = mrp_qty - spl_qty
        # if bal_qty>0:
        #     production.update({'product_qty':bal_qty})
        # row = 0
        # for line in split_line:
        #     if (bal_qty == 0) and (row == 0):
        #         production.update({'product_qty':line.product_qty})
        #     else:
        #         mrp_production = self.env['mrp.production'].create(self.mrp_values(None,production.name,production.product_id.id,line.product_qty,production.product_uom_id.id,production.bom_id.id,line.date_planned_start,line.date_planned_finished,production.shade,production.finish,production.sizein,production.sizecm))
        #         mrp_production.move_raw_ids.create(mrp_production._get_moves_raw_values())
        #         mrp_production._onchange_workorder_ids()
        #         mrp_production._create_update_move_finished()
        #     row += 1

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

