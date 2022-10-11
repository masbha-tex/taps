from odoo import fields, models, tools, api


class Inventory(models.Model):
    _name = "stock.opening.closing"
    _auto = False
    _description = "Stock Opening & Closing Report"
    #_order = "date desc, id desc"
    
    
    product_id = fields.Many2one('product.product', string='Item', readonly=True)
    #product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')
    product_category = fields.Many2one('category.type', string='Category', related='product_id.categ_type')
    product_parent_category = fields.Many2one('category.type', string='Product', related='product_category.parent_id')
    
    lot_id = fields.Many2one('stock.production.lot', string='Invoice', readonly=True)
    rejected_lot = fields.Boolean(string='Rejected', related='lot_id.rejected', readonly=True)
    lot_price = fields.Float(string='Price', readonly=True)
    
    opening_qty = fields.Float(string='Opening Quantity', readonly=True)
    opening_value = fields.Float(string='Opening Value', readonly=True)
    receive_qty = fields.Float(string='Receive Quantity', readonly=True)
    receive_value = fields.Float(string='Receive Value', readonly=True)
    issue_qty = fields.Float(string='Issue Quantity', readonly=True)
    issue_value = fields.Float(string='Issue Value', readonly=True)
    cloing_qty = fields.Float(string='Closing Quantity', readonly=True)
    cloing_value = fields.Float(string='Closing Value', readonly=True)
    
    company_id = fields.Many2one('res.company', readonly=True)
    
    
    def init(self):
        """ """
        tools.drop_view_if_exists(self._cr, 'stock_opening_closing')
        query = """
CREATE or REPLACE VIEW stock_opening_closing AS (
WITH
    existing_sm (id, product_id, product_qty, date, state, company_id, whs_id, whd_id, ls_usage, ld_usage) AS (
        SELECT m.id, m.product_id, m.product_qty, m.date, m.state, m.company_id, whs.id, whd.id, ls.usage, ld.usage
        FROM stock_move m
        LEFT JOIN stock_location ls on (ls.id=m.location_id)
        LEFT JOIN stock_location ld on (ld.id=m.location_dest_id)
        LEFT JOIN stock_warehouse whs ON ls.parent_path like concat('%/', whs.view_location_id, '/%')
        LEFT JOIN stock_warehouse whd ON ld.parent_path like concat('%/', whd.view_location_id, '/%')
        LEFT JOIN product_product pp on pp.id=m.product_id
        LEFT JOIN product_template pt on pt.id=pp.product_tmpl_id
        WHERE pt.type = 'product' AND
            (whs.id IS NOT NULL OR whd.id IS NOT NULL) AND
            (whs.id IS NULL OR whd.id IS NULL OR whs.id != whd.id) AND
            m.product_qty != 0 AND
            m.state NOT IN ('draft', 'cancel') AND
            (m.state != 'done' or m.date >= ((now() at time zone 'utc')::date - interval '3month'))
    ),
    all_sm (id, product_id, product_qty, date, state, company_id, whs_id, whd_id, ls_usage, ld_usage) AS (
        SELECT sm.id, sm.product_id, 
            CASE 
                WHEN is_duplicated = 0 THEN sm.product_qty
                WHEN sm.whs_id IS NOT NULL AND sm.whd_id IS NOT NULL AND sm.whs_id != sm.whd_id THEN sm.product_qty
                ELSE 0
            END, 
            sm.date, sm.state, sm.company_id,
            CASE WHEN is_duplicated = 0 THEN sm.whs_id END,
            CASE 
                WHEN is_duplicated = 0 AND NOT (sm.whs_id IS NOT NULL AND sm.whd_id IS NOT NULL AND sm.whs_id != sm.whd_id) THEN sm.whd_id 
                WHEN is_duplicated = 1 AND (sm.whs_id IS NOT NULL AND sm.whd_id IS NOT NULL AND sm.whs_id != sm.whd_id) THEN sm.whd_id 
            END,
            CASE WHEN is_duplicated = 0 THEN sm.ls_usage END,
            CASE 
                WHEN is_duplicated = 0 AND NOT (sm.whs_id IS NOT NULL AND sm.whd_id IS NOT NULL AND sm.whs_id != sm.whd_id) THEN sm.ld_usage 
                WHEN is_duplicated = 1 AND (sm.whs_id IS NOT NULL AND sm.whd_id IS NOT NULL AND sm.whs_id != sm.whd_id) THEN sm.ld_usage
            END
        FROM
            GENERATE_SERIES(0, 1, 1) is_duplicated,
            existing_sm sm
    )
SELECT
    MIN(id) as id,
    product_id,
    state,
    date,
    sum(product_qty) as product_qty,
    company_id,
    warehouse_id
FROM (SELECT
        m.id,
        m.product_id,
        CASE
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL THEN 'out'
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL THEN 'in'
        END AS state,
        m.date::date AS date,
        CASE
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL THEN -m.product_qty
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL THEN m.product_qty
        END AS product_qty,
        m.company_id,
        CASE
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL THEN m.whs_id
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL THEN m.whd_id
        END AS warehouse_id
    FROM
        all_sm m
    WHERE
        m.product_qty != 0 AND
        m.state != 'done'
    UNION ALL
    SELECT
        -q.id as id,
        q.product_id,
        'forecast' as state,
        date.*::date,
        q.quantity as product_qty,
        q.company_id,
        wh.id as warehouse_id
    FROM
        GENERATE_SERIES((now() at time zone 'utc')::date - interval '3month',
        (now() at time zone 'utc')::date + interval '3 month', '1 day'::interval) date,
        stock_quant q
    LEFT JOIN stock_location l on (l.id=q.location_id)
    LEFT JOIN stock_warehouse wh ON l.parent_path like concat('%/', wh.view_location_id, '/%')
    WHERE
        (l.usage = 'internal' AND wh.id IS NOT NULL) OR
        l.usage = 'transit'
    UNION ALL
    SELECT
        m.id,
        m.product_id,
        'forecast' as state,
        GENERATE_SERIES(
        CASE
            WHEN m.state = 'done' THEN (now() at time zone 'utc')::date - interval '3month'
            ELSE m.date::date
        END,
        CASE
            WHEN m.state != 'done' THEN (now() at time zone 'utc')::date + interval '3 month'
            ELSE m.date::date - interval '1 day'
        END, '1 day'::interval)::date date,
        CASE
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL AND m.state = 'done' THEN m.product_qty
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL AND m.state = 'done' THEN -m.product_qty
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL THEN -m.product_qty
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL THEN m.product_qty
        END AS product_qty,
        m.company_id,
        CASE
            WHEN m.whs_id IS NOT NULL AND m.whd_id IS NULL THEN m.whs_id
            WHEN m.whd_id IS NOT NULL AND m.whs_id IS NULL THEN m.whd_id
        END AS warehouse_id
    FROM
        all_sm m
    WHERE
        m.product_qty != 0) AS forecast_qty
GROUP BY product_id, state, date, company_id, warehouse_id
);
"""
        self.env.cr.execute(query)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        for i in range(len(domain)):
            if domain[i][0] == 'product_tmpl_id' and domain[i][1] in ('=', 'in'):
                tmpl = self.env['product.template'].browse(domain[i][2])
                # Avoid the subquery done for the related, the postgresql will plan better with the SQL view
                # and then improve a lot the performance for the forecasted report of the product template.
                domain[i] = ('product_id', 'in', tmpl.with_context(active_test=False).product_variant_ids.ids)
        return super().read_group(domain, fields, groupby, offset, limit, orderby, lazy)    