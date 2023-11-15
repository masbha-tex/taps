# -*- coding: utf-8 -*-
# from odoo import http


# class TapsDocuments(http.Controller):
#     @http.route('/taps_documents/taps_documents/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_documents/taps_documents/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_documents.listing', {
#             'root': '/taps_documents/taps_documents',
#             'objects': http.request.env['taps_documents.taps_documents'].search([]),
#         })

#     @http.route('/taps_documents/taps_documents/objects/<model("taps_documents.taps_documents"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_documents.object', {
#             'object': obj
#         })
