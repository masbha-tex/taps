from odoo import http
from odoo.http import request

class SaleOrderLineController(http.Controller):

    # @http.route('/web#id=<int:new_line_id>&view_type=form&model=sale.order.line&action=<int:action_id>', type='http', auth="public")
    # def redirect_to_sale_order_line_view(self, new_line_id, action_id):
    #     return request.env.ref('sale.view_order_line_tree').read()[0]

    # class MyController(http.Controller):
    # @http.route('/taps_sale/pie_chart', type='http', auth='public', website=True)
    # def pie_chart(self, **kw):
    #     # Fetch the data you want to visualize
    #     data = {...}  # Replace this with your actual data

    #     return request.render('taps_sale.pie_chart_template', {'data': data})
