# -*- coding: utf-8 -*-
# from odoo import http


# class BusinessExcellence(http.Controller):
#     @http.route('/business_excellence/business_excellence/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/business_excellence/business_excellence/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('business_excellence.listing', {
#             'root': '/business_excellence/business_excellence',
#             'objects': http.request.env['business_excellence.business_excellence'].search([]),
#         })

#     @http.route('/business_excellence/business_excellence/objects/<model("business_excellence.business_excellence"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('business_excellence.object', {
#             'object': obj
#         })
