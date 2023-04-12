from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class OrderFlow(models.Model):
    _name = "order.flow"
    _auto = False
    _description = "Sale Order Flow"
    
    check_id = fields.Many2one('sale.order', string='Check Reference')
    name = fields.Char(related='check_id.name',string='Sale Orde')
    # Pi_number = fields.Char(related='check_id.pi_number',string='Pi')
    pi_type = fields.Selection(related='check_id.pi_type',string='Type')
    sale_representative = fields.Many2one(related='check_id.sale_representative',string='Sales')
    date_order = fields.Datetime(related='check_id.date_order',string='Date')
    # sale_representative = fields.Char(related='representative_id.name', string='Sales Person')
    # order_ref = fields.Many2one('sale.order', string='Sale Order')
#     order_id = fields.Many2one('sale.order', string='OA Number')
#     pi_number = fields.Char(string='PI No.')
#     name = fields.Text(string='Description')
#     buyer_name = fields.Many2one('sale.buyer', related="order_id.buyer_name", string='Buyer Name')
#     sequence = fields.Integer(string='Sequence')
#     price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
#     price_subtotal = fields.Monetary(string='Subtotal')
#     price_total = fields.Monetary(string='Total')
#     product_id = fields.Many2one('product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]", change_default=True, ondelete='restrict', check_company=True)
#     product_template_id = fields.Many2one('product.template', string='Product Template', related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
#     product_name = fields.Char(related='product_template_id.name', string='Product Name')
#     product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure')
#     product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
#     product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
#     qty_delivered_method = fields.Selection([
#         ('manual', 'Manual'),
#         ('analytic', 'Analytic From Expenses')
#     ], string="Method to update delivered qty", compute='_compute_qty_delivered_method', compute_sudo=True, readonly=True)
#     qty_delivered = fields.Float('Delivered Quantity', copy=False, compute='_compute_qty_delivered', inverse='_inverse_qty_delivered', compute_sudo=True, digits='Product Unit of Measure', default=0.0)
#     qty_delivered_manual = fields.Float('Delivered Manually', copy=False, digits='Product Unit of Measure', default=0.0)

#     salesman_id = fields.Many2one('res.users',string='Salesperson',readonly=True)
#     currency_id = fields.Many2one('res.currency', string='Currency', readonly=True)
#     company_id = fields.Many2one('res.company', string='Company',readonly=True, index=True)
#     order_partner_id = fields.Many2one('res.partner',string='Customer', readonly=True)
    
    
    # rm_consumption = fields.Float('RM Consumption', compute='_compute_rm_consumption_value', digits='Product Price', default=0.0)
    
    
#     topbottom = fields.Text(string='Top/Bottom')
#     slidercode = fields.Text(string='Slider Code')
#     slidercodesfg = fields.Text(string='Slider Code (SFG)')
#     finish = fields.Text(string='Finish')
#     shade = fields.Text(string='Shade')
#     sizein = fields.Text(string='Size (Inch)')
#     sizecm = fields.Text(string='Size (CM)')
#     sizemm = fields.Text(string='Size (MM)')
    
#     dyedtape = fields.Text(string='Dyed Tape')
#     ptopfinish = fields.Text(string='Plated Top Finish')
#     pbotomfinish = fields.Text(string='Plated Bottom Finish')
#     ppinboxfinish = fields.Text(string='Plated Pin-Box Finish')
#     dippingfinish = fields.Text(string='Dipping Finish')
#     gap = fields.Text(string='Gap')
    
#     logoref = fields.Text(string='Logo & Ref')
#     shapefin = fields.Text(string='Shape Finish')
#     bcdpart = fields.Text(string='BCD Part Material Type / Size')
#     nailmat = fields.Text(string='Nail Material / Type / Shape / Size')
#     nailcap = fields.Text(string='Nail Cap Logo')
#     fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)')
#     nu1washer = fields.Text(string='1 NO. Washer Material & Size')
#     nu2washer = fields.Text(string='2 NO. Washer Material & Size')
#     bom_id = fields.Integer('Bom Id', copy=True)
    
    #company_id = fields.Many2one('res.company', readonly=True) SFG_
#     def _compute_rm_consumption_value(self):
#         for order in self:
#             mo = self.env['mrp.production'].search([('sale_order_line','=',order.id)])
#             production_id = mo.mapped('id')
#             #stock_move = self.env['stock.move'].search([('origin','in',(mo)),('bom_lin_id','is not','')])
#             stock_move_line = self.env['stock.move.line'].search([('production_id','in',(production_id)),('lot_id','!=','')])
#             #stock_move_line = stock_move_l.filtered(lambda inv: inv.production_id in (production_id) and inv.order_id.bom_lin_id != None and inv.lot_id != None)
#             #raise UserError((production_id,stock_move_line.id))
#             sel = 0
#             consumption = 0.0
#             if stock_move_line:
#                 for rm in stock_move_line:
#                     consumption += (rm.qty_done * rm.lot_id.unit_price)
#                     #raise UserError((rm.qty_done,rm.lot_id.unit_price))
            
#             order.rm_consumption = consumption
    
    def init(self):
        tools.drop_view_if_exists(self._cr, 'order_flow')
        
        query = """
        CREATE or REPLACE VIEW order_flow AS (
        select row_number() OVER() AS id,id as check_id,name,pi_type,sale_representative,date_order



        from sale_order where state='sale' and sales_type='sale'
        )
        """
        self.env.cr.execute(query)