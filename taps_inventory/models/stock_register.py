# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.tools.misc import format_datetime
from odoo.exceptions import UserError, ValidationError

class taps_inventory(models.Model):
    _inherit = 'stock.valuation.layer'
    _description = 'Stok Valuation'
    
    schedule_date = fields.Datetime('Schedule Date',readonly=True)


    def set_schedule_date(self, productid, moveid, createdate):
        productid=int(productid)
        moveid=int(moveid)
        getvaluation = self.env['stock.valuation.layer'].search([('stock_move_id', '=', moveid),('product_id', '=', productid)])
        move_line = self.env['stock.move.line'].search([('move_id', '=', moveid),('product_id', '=', productid)])
        
        if len(move_line) >= 1:
            getmove_line = move_line.sorted(key = 'id')[:1]
            sc_date = getmove_line.x_studio_schedule_date
            if len(getvaluation) == 1:
                if sc_date:
                    getvaluation[-1].write({'schedule_date':sc_date})
                else:
                    getvaluation[-1].write({'schedule_date':createdate})                    

class StockQuantityHistory(models.TransientModel):
    _inherit = 'stock.quantity.history'

    def open_at_date(self):
        active_model = self.env.context.get('active_model')
        if active_model == 'stock.valuation.layer':
            action = self.env["ir.actions.actions"]._for_xml_id("stock_account.stock_valuation_layer_action")
            action['domain'] = [('schedule_date', '<=', self.inventory_datetime), ('product_id.type', '=', 'product')]
            action['display_name'] = format_datetime(self.env, self.inventory_datetime)
            return action

        return super(StockQuantityHistory, self).open_at_date()