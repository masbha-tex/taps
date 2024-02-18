from odoo import http
from odoo.http import request

class ResPartnerController(http.Controller):

    @http.route('/open_similar_customers_popup', type='json', auth='user')
    def get_similar_customers(self, customer_name, **kw):
        context = kw.get('context', {})
        similar_customers = request.env['res.partner'].search([('name', 'ilike', customer_name)])
        return similar_customers.mapped('name')