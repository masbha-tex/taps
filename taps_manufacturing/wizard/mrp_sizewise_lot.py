import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import _, api, fields, models
import math

from typing import List, Union

_logger = logging.getLogger(__name__)


class MrpSizewiseLot(models.TransientModel):
    _name = 'mrp.sizewiselot'
    _description = 'Mrp Lot'
    _check_company_auto = True

    oa_id = fields.Text(string='OA', readonly=True)
    item = fields.Text(string='Item', readonly=True)
    shade = fields.Text(string='Shade', readonly=True)
    work_center = fields.Many2one('mrp.workcenter', string='Create From', readonly=True)
    material_qty = fields.Float('Tape Qty',digits='Product Unit of Measure', readonly=True)
    lot_line = fields.One2many('sizewiselot.line', 'lot_id',  string='Lot List',copy=True, auto_join=True)
    full_qty = fields.Boolean(readonly=False, string='Full Qty', default=False)

    @api.depends('lot_line.size_total')
    def _get_tape_bylots(self):
        for plan in self:
            plan.tape_qty = sum( (line.tape_con/line.qty)*line.size_total for line in plan.lot_line)
            

    tape_qty = fields.Float('Tape Consume',digits='Product Unit of Measure', readonly=False, store=True, default=0.0, compute='_get_tape_bylots') 

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_ids")
        operation = self.env[""+active_model+""].browse(active_id)
        orderline = self.env['manufacturing.order'].search([('oa_id', '=', operation[0].oa_id.id),('shade','=',operation[0].shade),('dyeing_plan','!=',None)])#.sorted(key = 'id')
        orderline_values = []

        # grouped_orderline = orderline.groupby(['size'])
        # for key, group in grouped_orderline.items():
        #     size, shade = key
        sizes = []

        for lines in orderline:
            size = lines.sizein
            if size == 'N/A':
                size = lines.sizecm
            if size not in sizes:
                orders = orderline.filtered(lambda p: p.sizein == size or p.sizecm == size)
                mrp_line = ','.join([str(i) for i in sorted(orders.ids)])
                sale_lines = ','.join([str(i) for i in sorted(orders.sale_order_line.ids)])
                tape_con = sum(orders.mapped('tape_con'))
                op_etails = self.env['operation.details'].search([('oa_id','=',operation[0].oa_id.id),('shade','=',operation[0].shade),('next_operation','=','Assembly Output')])
                op_etails = op_etails.filtered(lambda p: p.sizein == size or p.sizecm == size)
                
                actual_qty = sum(orders.mapped('balance_qty'))
                balance_qty = 0
                if op_etails:
                    balance_qty = actual_qty - sum(op_etails.mapped('qty'))
                else:
                    balance_qty = actual_qty

                    
                # found_values = [value for value in mrp_line if value in op_etails.mrp_lines]
                # raise UserError((found_values[0].name))
                orderline_values.append((0, 0, {
                    'mrp_line': mrp_line,
                    'sale_lines': sale_lines,
                    'sizein': lines.sizein,
                    'sizecm': lines.sizecm,
                    'gap': lines.gap,
                    'tape_con': tape_con,
                    'qty': actual_qty,
                    'balance_qty': balance_qty,
                    }))
                sizes.append(size)
            
        res.update({'oa_id': operation[0].oa_id.name,
                    'item': operation[0].fg_categ_type,
                    'shade': operation[0].shade,
                    'work_center': operation[0].work_center.id,
                    'material_qty': sum(operation.mapped('qty')),
                    'lot_line': orderline_values,#[(5, 0)] + [(0, 0, value) for value in orderline_values]
                    })
        return res 
            
    def done_mo_lot(self):
        # raise UserError((self.lot_line[0].mrp_line))
        active_model = self.env.context.get("active_model")
        ope_id = self.env.context.get("active_ids")
        return self.env['operation.details'].set_sizewiselot(active_model,ope_id,self.tape_qty,self.lot_line)
    
    @api.onchange('full_qty')
    def _onchange_qty_selection(self):
        if self.full_qty:
            if self.lot_line:
                for ml in self.lot_line:
                    if ml.balance_qty>0:
                        l_cap = 4000
                        if ml.lot_capacity>0:
                            l_cap = ml.lot_capacity
                        l_lots = math.ceil(ml.balance_qty/l_cap)
                        ml.update({'material_qty':ml.balance_qty,'lots':l_lots})
                    else:
                        raise UserError(('Machine and Quantity Required'))
                    
            else:
                raise UserError(('Data missing'))          


class SizewiseLotLine(models.TransientModel):
    _name = 'sizewiselot.line'
    _description = 'Lot Details'
    _check_company_auto = True

    lot_id = fields.Many2one('mrp.sizewiselot', string='Lot ID', ondelete='cascade', index=True, copy=False)
    mrp_line = fields.Char(string='Mrp Id', readonly=False)
    sale_lines = fields.Char(string='Sale Ids', readonly=False)
    # fields.Many2one('manufacturing.order', string='Mrp Id', readonly=False)
    sizein = fields.Char(string='Size (Inch)', readonly=True)
    sizecm = fields.Char(string='Size (CM)', readonly=True)
    gap = fields.Char(string='Gap', readonly=True)
    tape_con = fields.Float('Tape C.', readonly=True, digits='Product Unit of Measure')
    qty = fields.Float(string='Qty', readonly=True)
    balance_qty = fields.Float(string='Bl Qty', readonly=True)
    lot_capacity = fields.Float(string='Qty/Lot')
    lots = fields.Integer(string='Lots')
    # quantity_string = fields.Char(string="Quantities", readonly=False)
    size_total = fields.Float(string='Total', default = 0.0, readonly=False)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        
        # Set default values for fields in SizewiseLotLine
        res.update({
            'sizein': '',
            'sizecm': '',
            'gap': '',
            'tape_con': 0.0,  # Default Tape C. Value
            'qty': 0.0,  # Default Tape C. Value
            'balance_qty': 0.0,  # Default Qty Value
            'lot_capacity':0.0,
            'lots':0.0
            # 'quantity_string': '',
        })

        return res

    @api.onchange('lot_capacity')
    def _get_qty_bylots(self):
        for l in self:
            if l.lot_capacity>0:
                l_num = math.ceil(l.balance_qty/l.lot_capacity)
                l.lots = l_num
                if (l.lot_capacity*l_num)>l.balance_qty:
                    l.size_total = l.balance_qty
                else:
                    l.size_total = (l.lot_capacity*l_num)
        
    # @api.onchange('size_total')
    # def _get_tape_bylots(self):
    #     for l in self:
    #         quantity_strings = l.quantity_string.split('+')
    #         quantities = [int(qty) for qty in quantity_strings]
    #         qty = sum(quantities)
    #         if l.balance_qty < qty:
    #             raise UserError(('You can not excede balance qty'))
    #         else:
    #             l.size_total = qty
