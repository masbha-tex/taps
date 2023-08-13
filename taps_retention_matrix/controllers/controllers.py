# -*- coding: utf-8 -*-
# from odoo import http


# class TapsRetentionMatrix(http.Controller):
#     @http.route('/taps_retention_matrix/taps_retention_matrix/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_retention_matrix/taps_retention_matrix/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_retention_matrix.listing', {
#             'root': '/taps_retention_matrix/taps_retention_matrix',
#             'objects': http.request.env['taps_retention_matrix.taps_retention_matrix'].search([]),
#         })

#     @http.route('/taps_retention_matrix/taps_retention_matrix/objects/<model("taps_retention_matrix.taps_retention_matrix"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_retention_matrix.object', {
#             'object': obj
#         })
