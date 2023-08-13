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
from odoo.tools.safe_eval import safe_eval
import math

from typing import List, Union

_logger = logging.getLogger(__name__)


class BomVerification(models.TransientModel):
    _name = 'bom.verification'
    _description = 'Bom Verification'
    _check_company_auto = True

    
    product_tmpl_id = fields.Many2one('product.template', 'Product',  required=True)
    unit = fields.Selection([
        ('inch',	'Inch'),
        ('cm',	'CM'),
        ('mm',	'MM'),],
        string='unit', required=True, default='inch')
    size = fields.Float(required=True, string="size", default=1)
    uom_qty = fields.Float('Total Qty',digits='Product Unit of Measure')
    gap = fields.Text(string='Gap', readonly=True, default=1)
    veri_line = fields.One2many('bom.verification.line', 'verification_id', string='BOM Lines',copy=True, auto_join=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, index=True, default=lambda self: self.env.company)

    @api.onchange('product_tmpl_id', 'mo_qty','size','unit','uom_qty')
    def bom_change(self):
        wastage_percent = self.env['wastage.percent']
        
        formula = self.env['fg.product.formula'].search([('product_tmpl_id', '=', self.product_tmpl_id.id),('unit_type', '=', self.unit)])
        
        gap = self.product_tmpl_id.gap_inch
        if self.unit == 'cm':
            gap = self.product_tmpl_id.gap_cm
        self.gap = gap
        
        if formula:
            for f in formula:
                wastage_tape_cotton = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Cotton Tape')])
                wastage_tape = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Tape')])
    
                wastage_slider = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Slider')])
                wastage_top = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Top')])
                wastage_bottom = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Bottom')])
                wastage_wire = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Wire')])
                wastage_pinbox = wastage_percent.search([('product_type', '=', f.product_type),('material', '=', 'Pinbox')])
    
                con_tape_cotton = con_tape = con_wire = con_slider = con_top = con_bottom = con_pinboc = 0
                if f.tape_python_compute:
                    con_tape = safe_eval(f.tape_python_compute, {'s': self.size, 'g': self.gap})
                    if wastage_tape_cotton:
                        if wastage_tape_cotton.wastage>0:
                            con_tape_cotton += (con_tape*wastage_tape_cotton.wastage)/100
                    if wastage_tape:
                        if wastage_tape.wastage>0:
                            con_tape += (con_tape*wastage_tape.wastage)/100
                    con_tape_cotton = round(con_tape_cotton*self.uom_qty,4)
                    con_tape = round(con_tape*self.uom_qty,4)
    
                if f.wair_python_compute:
                    con_wire = safe_eval(f.wair_python_compute, {'s': self.size})
                    if wastage_wire:
                        if wastage_wire.wastage>0:
                            con_wire += (con_wire*wastage_wire.wastage)/100
                    con_wire = round(con_wire*self.uom_qty,4)
                if f.slider_python_compute:
                    con_slider = safe_eval(f.slider_python_compute)
                    if wastage_slider:
                        if wastage_slider.wastage>0:
                            con_slider += (con_slider*wastage_slider.wastage)/100
                    con_slider = round(con_slider*self.uom_qty,4)
                if f.twair_python_compute:
                    con_top = safe_eval(f.twair_python_compute)
                    if wastage_top:
                        if wastage_top.wastage>0:
                            con_top += (con_top*wastage_top.wastage)/100
                    con_top = round(con_top*self.uom_qty,4)
                if f.bwire_python_compute:
                    con_bottom = safe_eval(f.bwire_python_compute)
                    if wastage_bottom:
                        if wastage_bottom.wastage>0:
                            con_bottom += (con_bottom*wastage_bottom.wastage)/100
                    con_bottom = round(con_bottom*self.uom_qty,4)
                if f.tbwire_python_compute:
                    con_bottom = safe_eval(f.tbwire_python_compute)
                    if wastage_bottom:
                        if wastage_bottom.wastage>0:
                            con_bottom += (con_bottom*wastage_bottom.wastage)/100
                    con_bottom = round(con_bottom*self.uom_qty,4)
                if f.pinbox_python_compute:
                    con_pinbox = safe_eval(f.pinbox_python_compute)
                    if wastage_pinbox:
                        if wastage_pinbox.wastage>0:
                            con_pinbox += (con_pinbox*wastage_pinbox.wastage)/100
                    con_pinbox = round(con_pinbox*self.uom_qty,4)
                
                orderline_values = []
                orderline_values += [{
                    'verification_id':self.id,
                    'topbottom_type':f.topbottom_type,
                    'tape_con_cotton':con_tape_cotton,
                    'tape_con':con_tape,
                    'wire_con':con_wire,
                    'slider_con':con_slider,
                    'topwire_con':con_top,
                    'botomwire_con':con_bottom,
                    'pinbox_con':con_pinboc,
                    'total_cost':0,
                }]
                self.veri_line = [(5, 0)] + [(0, 0, value) for value in orderline_values]
    

class BomVerificationLine(models.TransientModel):
    _name = 'bom.verification.line'
    _description = 'Bom Verification'
    #_order = 'order_id, sequence, id'
    _check_company_auto = True

    
    verification_id = fields.Many2one('bom.verification', string='Verification ID', required=True, ondelete='cascade', index=True, copy=False)
    topbottom_type = fields.Text(string='Type')

    tape_con_cotton = fields.Float('Cotton Tape', required=True, digits='Unit Price', default=0.0)
    tape_con = fields.Float('Polister Tape', required=True, digits='Unit Price', default=0.0)
    slider_con = fields.Float('Slider Consumption', required=True, digits='Unit Price', default=0.0)
    topwire_con = fields.Float('Topwire Consumption', required=True, digits='Unit Price', default=0.0)
    botomwire_con = fields.Float('Botomwire Consumption', required=True, digits='Unit Price', default=0.0)
    tbwire_con = fields.Float('TBwire Consumption', required=True, digits='Unit Price', default=0.0)
    wire_con = fields.Float('Wire Consumption', required=True, digits='Unit Price', default=0.0)
    pinbox_con = fields.Float('Pinbox Consumption', required=True, digits='Unit Price', default=0.0)
    total_cost = fields.Float('Pinbox Consumption', required=True, digits='Unit Price', default=0.0)

    
