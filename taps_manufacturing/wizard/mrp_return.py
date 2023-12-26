import base64
import io
import logging
from psycopg2 import Error, OperationalError
from odoo.exceptions import UserError, ValidationError
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from odoo import _, api, fields, models
import math

class PackingReturn(models.TransientModel):
    _name = 'mrp.return'
    _description = 'Quantity Return'
    _check_company_auto = True
    
    oa_id = fields.Char(string='OA', readonly=True)
    item = fields.Char(string='Item', readonly=True)
    shade = fields.Text(string='Shade', readonly=True)
    size = fields.Char(string='Size', readonly=True)
    done_qty = fields.Float(string='Qty', digits='Product Unit of Measure', readonly=True)
    return_qty = fields.Float(string='Return Qty', default=0.0, digits='Product Unit of Measure',required=True)
    
    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_model = self.env.context.get("active_model")
        active_id = self.env.context.get("active_id")
        production = self.env["operation.details"].browse(active_id)
        res["oa_id"] = production.oa_id.name
        res["item"] = production.fg_categ_type
        res["shade"] = production.shade
        res["size"] = production.sizecm
        res["done_qty"] = production.qty
        return res 
            
    def done_mo_return(self):
        if self.done_qty < self.return_qty:
            raise UserError(('You can not return more then qty'))
            return
        mo_id = self.env.context.get("active_id")
        production = self.env["operation.details"].browse(mo_id)
        
        oa_id = production.oa_id.id
        oa = production.oa_id.name
        return_qty = self.return_qty
        qty_exist = production.qty - return_qty
        
        mrp_lines = [int(id_str) for id_str in production.mrp_lines.split(',')]
        mrp_data = self.env["manufacturing.order"].browse(mrp_lines)
        pr_pac_qty = mrp_data.product_template_id.pack_qty
        pack_qty = production.pack_qty
        fraction_pc_of_pack = production.fr_pcs_pack
        mrplines = production.mrp_lines
        mrp_id = int(production.mrp_lines)
        if pr_pac_qty:
            pack_qty = math.ceil(qty_exist/pr_pac_qty)
            fraction_pc_of_pack = round((((qty_exist/pr_pac_qty) % 1)*pr_pac_qty),0)
            
        
        query = """update operation_details set done_qty = done_qty - %s,balance_qty = balance_qty + %s,ac_balance_qty = ac_balance_qty + %s,state = 'waiting' where oa_id = %s and next_operation = 'Packing Output' and mrp_lines = %s; 
update manufacturing_order set done_qty = done_qty - %s,balance_qty = balance_qty + %s where oa_id = %s and id = %s;
update manufacturing_order set oa_total_balance = oa_total_balance + %s where oa_id = %s;
update manufacturing_order set closing_date = case when oa_total_balance > 0 then null else closing_date end, state = case when oa_total_balance > 0 then 'partial' else state end where oa_id = %s;"""

        
        self._cr.execute(query, (return_qty, return_qty,return_qty,oa_id,mrplines,return_qty,return_qty,oa_id,mrp_id,return_qty,oa_id,oa_id))
        # raise UserError((query))
        
        pack_return = production.update({'qty': qty_exist, 'return_qty':production.return_qty + return_qty,'pack_qty':pack_qty,'fr_pcs_pack': fraction_pc_of_pack})

        # stockmove_line = self.env["stock.move.line"].search([('origin','=',oa),('state','not in',('draft','done','cancel'))])
        
        # picking = self.env["stock.picking"].search([('origin','=',oa),('state','not in',('draft','done','cancel'))])
        # if picking:
        #     picking.action_assign()
        
        return
