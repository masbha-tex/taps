import base64
import io
import logging

from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from odoo import models, fields, api, _
from odoo import tools

_logger = logging.getLogger(__name__)


class StockRegisterReport(models.TransientModel):
    _name = 'stock.register.wiz'
    _description = "This is for Stock Register Report"
    
    from_date = fields.Date('From')
    to_date = fields.Date('To', default=fields.Date.context_today)
    
    ReportRegister.init(from_date,to_date)

class ReportRegister(models.Model):
    _name = 'stock.register.report'
    _auto = False
    _description = "This is for Stock Register Report"
    #_order = 'punching_day desc'

    product_id = fields.Many2one('product.product', 'Product', readonly=True)
    category_id = fields.Many2one('product.category', 'Product Category', readonly=True)
    product_tmpl_id = fields.Many2one('product.template', related='product_id.product_tmpl_id')

    def init(self,from_date,to_date):
        raise UserError(('dkjslj'))
        tools.drop_view_if_exists(self._cr, 'stock_register_report')
        query = """
            create or replace view stock_register_report as (
            select 
            t.categ_id as category_id,
            a.product_id,
            a.description,
            a.schedule_date,
            a.stock_move_id,
            (select sum(quantity) from stock_valuation_layer vd where vd.product_id=a.product_id and 
            vd.schedule_date=a.schedule_date and vd.stock_move_id=a.stock_move_id and vd.quantity>=0) as Received_Qty,
            (select sum(value) from stock_valuation_layer vd where vd.product_id=a.product_id and 
            vd.schedule_date=a.schedule_date and vd.stock_move_id=a.stock_move_id and vd.quantity>=0) as Received_Value,
            (select sum(quantity) from stock_valuation_layer vd where vd.product_id=a.product_id and 
            vd.schedule_date=a.schedule_date and vd.stock_move_id=a.stock_move_id and vd.quantity<0) as Issued_Qty,
            (select sum(value) from stock_valuation_layer vd where vd.product_id=a.product_id and 
            vd.schedule_date=a.schedule_date and vd.stock_move_id=a.stock_move_id and vd.quantity<0) as Issued_Value,
            sum(quantity) as Closing_Qty,
            sum(value) as Closing_Value
            from stock_valuation_layer a
            inner join product_product p on (a.product_id=p.id)
            inner join product_template t on (p.product_tmpl_id=t.id)
            GROUP BY
            t.categ_id,
            a.product_id,
            a.description,
            a.schedule_date,
            a.stock_move_id
            )
            """
        self._cr.execute(query)