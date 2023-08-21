from odoo import http
from odoo.http import request

class SaleOrderLineController(http.Controller):

    @http.route('/web#id=<int:new_line_id>&view_type=form&model=sale.order.line&action=<int:action_id>', type='http', auth="public")
    def redirect_to_sale_order_line_view(self, new_line_id, action_id):
        return request.env.ref('sale.view_order_line_tree').read()[0]
