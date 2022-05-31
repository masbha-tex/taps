from odoo import models, fields, api, tools, _
from odoo.tools.misc import format_datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

class PickingVendorNameINT(models.Model):
    _inherit = 'stock.picking'
    partner_name = fields.Char(rreadonly=True, store=True, string='Vendor Name', compute='compute_partner')
    
    def compute_partner(self):
        for rec in self:
            po = self.env['purchase.order'].search([('name', '=', rec.origin)])
            if po:
                partner = self.env['res.partner'].search([('id', '=', po.partner_id.id)])
                rec.partner_name = partner.name
            
    def createupdate_qc(self,id,name,company,state):
        if "/INT/" in name and state=="assigned":
            transferdata = self.env['stock.move.line'].search([('picking_id', '=', id)]).sorted(key = 'id')
            if transferdata:
                qcdata = self.env['quality.check'].search([('picking_id', '=', id)]).sorted(key = 'id')
                for tr in transferdata:
                    qcproduct = qcdata.search([('product_id', '=', tr.product_id.id),('lot_id', '=', False)])
                    qclotexist = qcdata.search([('product_id', '=', tr.product_id.id),('lot_id', '=', tr.lot_id.id)])
                    if qcproduct:
                        qcproduct.write({'lot_id': tr.lot_id.id})
                    elif qclotexist:
                        qty=1
                    else:
                        qcdata.create({'point_id': 4,
                                       'quality_state': 'none',
                                       'product_id': tr.product_id.id,
                                       'picking_id': id,
                                       'lot_id': tr.lot_id.id,
                                       'team_id': 1,
                                       'company_id': company.id,
                                       'test_type_id': 3})
                        
# name
# point_id
# quality_state
# product_id
# picking_id
# lot_id
# team_id
# company_id
# test_type_id
# create_uid
# create_date
# write_uid
# write_date
# measure
# measure_success
# x_studio_source_po
# x_studio_schedule_po_date
# x_studio_sample_qty                        
                    
                    
        




class IncludeCateTypeInPT(models.Model):
    _inherit = 'stock.move.line'
    parent_categ_type = fields.Char(related='product_id.categ_type.parent_id.name', related_sudo=False, readonly=True, store=True, string='Parent Category')
    category_type = fields.Char(related='product_id.categ_type.name', related_sudo=False, readonly=True, store=True, string='Category Type')    
    qty_onhand = fields.Float(related='lot_id.product_qty', readonly=True, store=True, string='Quantity')
    unit_price = fields.Float(related='product_id.standard_price', readonly=True, store=True, string='Price')
    value = fields.Float(compute='_compute_product_value', readonly=True, store=True, string='Value')
    duration = fields.Integer(string='Duration', compute='_compute_duration', store=True, readonly=True)
    pur_price = fields.Float(compute='_compute_purchase_price', readonly=True, string='Purchase Price')
    #pur_value = fields.Float(compute='_compute_purchase_value', readonly=True, string='Purchase Value')
    #product_id.categ_type.parent_id.name 
    @api.depends('product_id', 'product_uom_id', 'product_uom_qty')
    def _compute_product_value(self):
        for record in self:
            record['value'] = round(record.qty_onhand * record.unit_price,2)
            
    def _get_aggregated_product_quantities(self, **kwargs):
        """ Returns a dictionary of products (key = id+name+description+uom) and corresponding values of interest.

        Allows aggregation of data across separate move lines for the same product. This is expected to be useful
        in things such as delivery reports. Dict key is made as a combination of values we expect to want to group
        the products by (i.e. so data is not lost). This function purposely ignores lots/SNs because these are
        expected to already be properly grouped by line.

        returns: dictionary {product_id+name+description+uom: {product, name, description, qty_done, product_uom}, ...}
        """
        aggregated_move_lines = {}
        for move_line in self:
            name = move_line.product_id.display_name
            description = move_line.move_id.description_picking
            if description == name or description == move_line.product_id.name:
                description = False
            uom = move_line.product_uom_id
            line_key = str(move_line.product_id.id) + "_" + name + (description or "") + "uom " + str(uom.id)

            if line_key not in aggregated_move_lines:
                aggregated_move_lines[line_key] = {'name': name,
                                                   'description': description,
                                                   'qty_done': move_line.qty_done,
                                                   'qty_onhand': move_line.qty_onhand,
                                                   'value': move_line.value,
                                                   'product_uom': uom.name,
                                                   'product': move_line.product_id}
            else:
                aggregated_move_lines[line_key]['qty_done'] += move_line.qty_done
                aggregated_move_lines[line_key]['qty_onhand'] += move_line.qty_onhand
                aggregated_move_lines[line_key]['value'] += move_line.value
        return aggregated_move_lines
    
    @api.depends('product_id')
    def _compute_duration(self):
        for line in self:
            sc_date = line.create_date
            if line.x_studio_schedule_date:
                sc_date = line.x_studio_schedule_date
            x = datetime.now().replace(hour=0, minute =0, second = 0, microsecond = 0)
            y = sc_date.replace(hour=23, minute =59, second = 59, microsecond = 0)
            dur = x-y
            line.duration = dur.days+1
            
    def _update_duration(self):
        move_line = self.env['stock.move.line'].search([('id', '>', 0)])
        for record in move_line:
            sc_date = record.create_date
            if record.x_studio_schedule_date:
                sc_date = record.x_studio_schedule_date
            x = datetime.now().replace(hour=0, minute =0, second = 0, microsecond = 0)
            y = sc_date.replace(hour=23, minute =59, second = 59, microsecond = 0)
            dur = x-y
            record[-1].write({'duration' : dur.days+1})
            
    def _compute_purchase_price(self):
        for record in self:
            stock_v_layer = self.env['stock.valuation.layer'].search([('stock_move_id', '=', int(record.move_id)),('product_id', '=', int(record.product_id)),('description', 'like', '/IN/')])
            if stock_v_layer:
                record.pur_price = round(stock_v_layer.unit_cost,4)
            else:
                record.pur_price = 0.00
                
    #def _compute_purchase_value(self):
    #    for record in self:
    #        record['pur_value'] = round(record.qty_done * record.pur_price,2)