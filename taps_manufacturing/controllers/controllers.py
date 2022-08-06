# -*- coding: utf-8 -*-
# from odoo import http


# class TapsManufacturing(http.Controller):
#     @http.route('/taps_manufacturing/taps_manufacturing/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_manufacturing/taps_manufacturing/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_manufacturing.listing', {
#             'root': '/taps_manufacturing/taps_manufacturing',
#             'objects': http.request.env['taps_manufacturing.taps_manufacturing'].search([]),
#         })

#     @http.route('/taps_manufacturing/taps_manufacturing/objects/<model("taps_manufacturing.taps_manufacturing"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_manufacturing.object', {
#             'object': obj
#         })
