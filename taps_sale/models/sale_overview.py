from odoo import fields, models, tools, api
from datetime import date, datetime, time, timedelta
from odoo.tools import format_date
from odoo.exceptions import UserError, ValidationError

class SaleOverview(models.Model):
    _name = "sale.overview"
    _description = "Sale Overview"
    #_order = "date desc, id desc"
    
    
    
    order_id = fields.Many2one('sale.order', string='Order Reference')
    name = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    price_unit = fields.Float('Unit Price', required=True, digits='Product Price', default=0.0)
    price_subtotal = fields.Monetary(string='Subtotal')
    #price_tax = fields.Float(string='Total Tax')
    #price_total = fields.Monetary(string='Total')
    #price_reduce = fields.Float(string='Price Reduce', digits='Product Price')
    #tax_id = fields.Many2many('account.tax', string='Taxes', context={'active_test': False})
    #price_reduce_taxinc = fields.Monetary(compute='_get_price_reduce_tax', string='Price Reduce Tax inc', readonly=True, store=True)
    #price_reduce_taxexcl = fields.Monetary(compute='_get_price_reduce_notax', string='Price Reduce Tax excl', readonly=True, store=True)

    #discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('sale_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        change_default=True, ondelete='restrict', check_company=True)  # Unrequired company
    product_template_id = fields.Many2one(
        'product.template', string='Product Template',
        related="product_id.product_tmpl_id", domain=[('sale_ok', '=', True)])
    product_updatable = fields.Boolean(compute='_compute_product_updatable', string='Can Edit Product', readonly=True, default=True)
    product_uom_qty = fields.Float(string='Quantity', digits='Product Unit of Measure', required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', domain="[('category_id', '=', product_uom_category_id)]")
    product_uom_category_id = fields.Many2one(related='product_id.uom_id.category_id', readonly=True)
    #product_uom_readonly = fields.Boolean(compute='_compute_product_uom_readonly')
    #product_custom_attribute_value_ids = fields.One2many('product.attribute.custom.value', 'sale_order_line_id', string="Custom Values", copy=True)

    # M2M holding the values of product.attribute with create_variant field set to 'no_variant'
    # It allows keeping track of the extra_price associated to those attribute values and add them to the SO line description
    #product_no_variant_attribute_value_ids = fields.Many2many('product.template.attribute.value', string="Extra Values", ondelete='restrict')

    qty_delivered_method = fields.Selection([
        ('manual', 'Manual'),
        ('analytic', 'Analytic From Expenses')
    ], string="Method to update delivered qty", compute='_compute_qty_delivered_method', compute_sudo=True, store=True, readonly=True,
        help="According to product configuration, the delivered quantity can be automatically computed by mechanism :\n"
             "  - Manual: the quantity is set manually on the line\n"
             "  - Analytic From expenses: the quantity is the quantity sum from posted expenses\n"
             "  - Timesheet: the quantity is the sum of hours recorded on tasks linked to this sale line\n"
             "  - Stock Moves: the quantity comes from confirmed pickings\n")
    qty_delivered = fields.Float('Delivered Quantity', copy=False, compute='_compute_qty_delivered', inverse='_inverse_qty_delivered', compute_sudo=True, store=True, digits='Product Unit of Measure', default=0.0)
    qty_delivered_manual = fields.Float('Delivered Manually', copy=False, digits='Product Unit of Measure', default=0.0)

    salesman_id = fields.Many2one(related='order_id.user_id', store=True, string='Salesperson', readonly=True)
    currency_id = fields.Many2one(related='order_id.currency_id', depends=['order_id.currency_id'], store=True, string='Currency', readonly=True)
    company_id = fields.Many2one(related='order_id.company_id', string='Company', store=True, readonly=True, index=True)
    order_partner_id = fields.Many2one(related='order_id.partner_id', store=True, string='Customer', readonly=False)
    
    
    topbottom = fields.Text(string='Top/Bottom', store=True)
    slidercode = fields.Text(string='Slider Code', store=True)
    slidercodesfg = fields.Text(string='Slider Code (SFG)', store=True)
    finish = fields.Text(string='Finish', store=True)
    shade = fields.Text(string='Shade', store=True)
    sizein = fields.Text(string='Size (Inch)', store=True)
    sizecm = fields.Text(string='Size (CM)', store=True)
    sizemm = fields.Text(string='Size (MM)', store=True)
    
    dyedtape = fields.Text(string='Dyed Tape', store=True)
    ptopfinish = fields.Text(string='Plated Top Finish', store=True)
    pbotomfinish = fields.Text(string='Plated Bottom Finish', store=True)
    ppinboxfinish = fields.Text(string='Plated Pin-Box Finish', store=True)
    dippingfinish = fields.Text(string='Dipping Finish', store=True)
    gap = fields.Text(string='Gap', store=True)
    
    logoref = fields.Text(string='Logo & Ref', store=True)
    shapefin = fields.Text(string='Shape Finish', store=True)
    bcdpart = fields.Text(string='BCD Part Material Type / Size', store=True)
    nailmat = fields.Text(string='Nail Material / Type / Shape / Size', store=True)
    nailcap = fields.Text(string='Nail Cap Logo', store=True)
    fnamebcd = fields.Text(string='Finish Name ( BCD/NAIL/ NAIL CAP)', store=True)
    nu1washer = fields.Text(string='1 NO. Washer Material & Size', store=True)
    nu2washer = fields.Text(string='2 NO. Washer Material & Size', store=True)
    bom_id = fields.Integer('Bom Id', copy=True, store=True)
    
    #company_id = fields.Many2one('res.company', readonly=True)
    
    
    def init(self):
        #start_time = fields.datetime.now()
        #f_date = self.from_date
        #t_date = self.to_date
        #hour_from = 0.0
        #hour_to = 23.98
        #combine = datetime.combine
        #date_search = self.env['searching_date'] #(select from_date from searching_date)
        #from_date = date_search.from_date # (select to_date from searching_date)
        #to_date = date_search.to_date
        #from_date1,from_date2,from_date3,from_date4,from_dat5,to_date1,from_date6,to_date2,from_date7,to_date3,from_date8,to_date4,
        tools.drop_view_if_exists(self._cr, 'stock_opening_closing')
        query = """
        CREATE or REPLACE VIEW stock_opening_closing AS (
        select ROW_NUMBER () OVER (ORDER BY product_id) as id, product_id, categ_type as product_category,parent_id as parent_category,invoice as lot_id, rejected, avg(lot_price) as lot_price, sum(opening_qty) as opening_qty,
        case when avg(lot_price)>0 then sum(opening_qty)*avg(lot_price) else sum(opening_value) end as opening_value,
        sum(receive_qty) as receive_qty,
        case when avg(lot_price)>0 then sum(receive_qty)*avg(lot_price) else sum(receive_value) end as receive_value,
        sum(issue_qty) as issue_qty,
        case when avg(lot_price)>0 then sum(issue_qty)*avg(lot_price) else sum(issue_value) end as issue_value,
        sum(cloing_qty) as cloing_qty,
        case when avg(lot_price)>0 then sum(cloing_qty)*avg(lot_price) else sum(cloing_value) end as cloing_value 
        from(
        select
        product.id as product_id,pt.categ_type,catype.parent_id,lot.id as invoice,lot.rejected,
        
        (case when lot.id is not null then
        lot.unit_price else 0 end
        ) as lot_price,
        
        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done when a.quantity=0 then 0 else b.qty_done end),0) as op_qty from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<sd.from_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) when a.description like '%LC/%' then a.value else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<sd.from_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<sd.from_date) end
        ) as opening_value,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as re_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like '%/IN/%' or a.description like '%/OUT/%') and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like '%/IN/%' or a.description like '%/OUT/%')) end
        ) as receive_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as re_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where (a.description like '%/IN/%' or a.description like '%/OUT/%') and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and (a.description like '%/IN/%' or a.description like '%/OUT/%')) end
        ) as receive_value,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done else b.qty_done end),0) as isue_quantity from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like '%/MR/%' and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like '%/MR/%') end
        ) as issue_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) else (b.qty_done*a.unit_cost) end),0) as re_value from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where a.description like '%/MR/%' and b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date>=sd.from_date and a.schedule_date<=sd.to_date and a.description like '%/MR/%') end
        ) as issue_value,


        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -b.qty_done when a.quantity=0 then 0 else b.qty_done end),0) as op_qty from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(quantity),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_qty,

        (
        case when lot.id is not null then
        (select COALESCE(sum(case when a.quantity<0 then -(b.qty_done*a.unit_cost) when a.description like '%LC/%' then a.value else (b.qty_done*a.unit_cost) end),0) as op_val from stock_valuation_layer as a inner join stock_move_line as b on a.stock_move_id=b.move_id and a.product_id=b.product_id where b.lot_id=lot.id and  a.product_id=product.id and a.schedule_date<=sd.to_date)
        else (select COALESCE(sum(value),0) from stock_valuation_layer as a where a.product_id=product.id and a.schedule_date<=sd.to_date) end
        ) as cloing_value

        from product_product as product
        inner join product_template as pt on product.product_tmpl_id=pt.id
        inner join category_type as catype on pt.categ_type=catype.id
        left join category_type as pcatype on catype.parent_id=pcatype.id
        left join stock_production_lot as lot on product.id=lot.product_id
        left join searching_date as sd on 1=1
        where product.default_code like'R_%' or product.default_code like'S_%'
        ) as stock where (abs(stock.opening_qty)+abs(stock.receive_qty)+abs(stock.issue_qty))>0
        group by stock.product_id,stock.categ_type,stock.parent_id,stock.invoice,stock.rejected
        )
        """
        self.env.cr.execute(query)

#     @api.model
#     def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
#         for i in range(len(domain)):
#             if domain[i][0] == 'product_tmpl_id' and domain[i][1] in ('=', 'in'):
#                 tmpl = self.env['product.template'].browse(domain[i][2])
#                 # Avoid the subquery done for the related, the postgresql will plan better with the SQL view
#                 # and then improve a lot the performance for the forecasted report of the product template.
#                 domain[i] = ('product_id', 'in', tmpl.with_context(active_test=False).product_variant_ids.ids)
#         return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)