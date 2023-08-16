from odoo import models, fields, tools, api, _
from odoo.tools.misc import format_datetime
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_date
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta

# class taps_inventory(models.Model):
#     _inherit = 'stock.move.line'
#     _description = 'Stok Ageing'
    
#     duration = fields.Integer(string='Duration', compute='_compute_duration', readonly=True)
#     #x_studio_schedule_date
    
#     @api.depends('product_id', 'x_studio_schedule_date')
#     def _compute_duration(self):
#         for line in self:
#             dur = datetime.now()-line.x_studio_schedule_date
#             line.duration = dur.days
            
            
class Ageing(models.Model):
    _name = "stock.ageing"
    _description = "Stock Ageing"
    _check_company_auto = True
    #_auto = False
    #_order = "date desc, id desc"
    
    
    product_id = fields.Many2one('product.product', string='Item', readonly=True)
    #product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    product_category = fields.Many2one('category.type', string='Category')
    parent_category = fields.Many2one('category.type', string='Product')
    
    lot_id = fields.Many2one('stock.production.lot', string='Invoice', readonly=True)
    rejected = fields.Text(string='Rejected', readonly=True)
    lot_price = fields.Float(string='Price', readonly=True, digits='Unit Price')
    pur_price = fields.Float(string='Pur Price', readonly=True, digits='Unit Price')
    landed_cost = fields.Float(string='Landed Cost', readonly=True, digits='Unit Price')
    
    # opening_qty = fields.Float(string='Opening Quantity', readonly=True)
    # opening_value = fields.Float(string='Opening Value', readonly=True)
    # receive_qty = fields.Float(string='Receive Quantity', readonly=True)
    # receive_value = fields.Float(string='Receive Value', readonly=True)
    # issue_qty = fields.Float(string='Issue Quantity', readonly=True)
    # issue_value = fields.Float(string='Issue Value', readonly=True)
    receive_date = fields.Datetime('Receive Date', readonly=True)
    duration = fields.Integer(string='Duration', readonly=True)
    
    cloing_qty = fields.Float(string='Quantity', readonly=True)
    cloing_value = fields.Float(string='Value', readonly=True)
    
    
    slot_1 = fields.Float(string='0-30', readonly=True)
    slot_2 = fields.Float(string='31-60', readonly=True)
    slot_3 = fields.Float(string='61-90', readonly=True)
    slot_4 = fields.Float(string='91-180', readonly=True)
    slot_5 = fields.Float(string='181-365', readonly=True)
    slot_6 = fields.Float(string='365+', readonly=True)
    
    company_id = fields.Many2one('res.company', 'Company', related='product_id.company_id', readonly=True, index=True, default=lambda self: self.env.company.id)