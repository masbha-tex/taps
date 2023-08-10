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


class OperationDetails(models.Model):
    _name = "operation.details"
    _description = "Operation Details"
    _check_company_auto = True

    code = fields.Char(string='Code', store=True)
    mrp_lines = fields.Char(string='Mrp lines', store=True)
    sale_lines = fields.Char(string='Sale lines', store=True)
    
    mrp_line = fields.Many2one('manufacturing.order', string='Mrp Id', store=True, readonly=True)
    sale_order_line = fields.Many2one('sale.order.line', string='Sale Order Line', store=True, readonly=True)
    parent_id = fields.Many2one('operation.details', 'Parent Operation', index=True, ondelete='cascade')
    
    oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    company_id = fields.Many2one('res.company', related='oa_id.company_id', string='Company', readonly=True, store=True)

    product_template_id = fields.Many2one('product.template', domain=[('sale_ok', '=', True)])
    fg_categ_type = fields.Selection(related='product_template_id.fg_categ_type')
    
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', related='product_template_id.uom_id')
    
    date_order = fields.Datetime(string='Order Date', related='oa_id.date_order', readonly=True)
    action_date = fields.Datetime(string='Action Date', readonly=True)
    partner_id = fields.Many2one('res.partner', related='oa_id.partner_id', string='Customer', readonly=True)
    #buyer_name = fields.Many2one('sale.buyer', related='oa_id.buyer_name', string='Buyer', readonly=True)
    
    slidercodesfg = fields.Char(string='Slider Code (SFG)', store=True, readonly=True)
    finish = fields.Char(string='Finish', store=True, readonly=True)
    shade = fields.Char(string='Shade', store=True, readonly=True)

    
    operation_of = fields.Selection([
        ('plan', 'Planning'),
        ('lot', 'Create Lot'),
        ('output', 'Output'),
        ('req', 'Requisition')],
        string='Operation Of')
    operation_by = fields.Text(string='Operation By', store=True)
    based_on = fields.Char(string='Based On', store=True)
    qty = fields.Float(string='Qty', readonly=False)
    done_qty = fields.Float(string='Qty Done', default=0.0, readonly=False)
    balance_qty = fields.Float(string='Balance', readonly=True, compute='get_balance')
    num_of_lots = fields.Integer(string='N. of Lots', readonly=True, compute='get_lots')
    # lot_ids = fields.Many2one('operation.details', compute='get_lots', string='Lots', copy=False, store=True)
    def get_balance(self):
        for s in self:
            s.balance_qty = s.qty - s.done_qty
    
    def get_lots(self):
        for s in self:
            count_lots = self.env['operation.details'].search_count([('parent_id', '=', s.id),('operation_of', '=', 'lot')])
            s.num_of_lots = count_lots
            #s.lot_ids = count_lots.mapped('id')
            
    def button_requisition(self):
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_requisition")
        action["domain"] = [('default_id','in',self.mapped('id'))]
        a = 'a'
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

    def button_createlot(self):
        self.ensure_one()
        self._check_company()
        action = self.env["ir.actions.actions"]._for_xml_id("taps_manufacturing.action_mrp_lot")
        #action["domain"] = [('default_id','=',self.mapped('id'))]
        return action
        


    def set_lot(self,ope_id,lot_line):
        operation = self.env["operation.details"].browse(ope_id)
        #raise UserError((operation.oa_id.id))
        if lot_line:
            for l in lot_line:
                ope = operation.create({'mrp_lines':None,
                                  'sale_lines':None,
                                  'mrp_line':None,
                                  'sale_order_line':None,
                                  'parent_id':ope_id,
                                  'oa_id':operation.oa_id.id,
                                  'product_template_id':operation.product_template_id.id,
                                  'action_date':datetime.now(),
                                  'shade':operation.shade,
                                  'finish':operation.finish,
                                  'slidercodesfg':operation.slidercodesfg,
                                  'operation_of':'lot',
                                  'operation_by':'dyeing',
                                  'based_on':'Lot Code',
                                  'qty':l.material_qty,
                                  'done_qty':0
                                 })
    def action_view_lots(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        
        result = self.env["ir.actions.actions"]._for_xml_id('taps_manufacturing.action_operation_details')
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'parent_id': self.id, 'operation_of': 'lot'}
        lots_ = self.env['operation.details'].search([('parent_id', '=', self.id),('operation_of', '=', 'lot')])
        lot_ids = lots_.mapped('id')
        #raise UserError((lot_ids))
        # choose the view_mode accordingly
        result['domain'] = "[('id','in',%s)]" % (lot_ids)
        return result


        
        # elif len(pick_ids) == 1:
        #     res = self.env.ref('stock.view_picking_form', False)
        #     form_view = [(res and res.id or False, 'form')]
        #     if 'views' in result:
        #         result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
        #     else:
        #         result['views'] = form_view
        #     result['res_id'] = pick_ids.id
                        
