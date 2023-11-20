# -*- coding: utf-8 -*-
# from odoo import http


# class GoogleSheetConnector(http.Controller):
#     @http.route('/google_sheet_connector/google_sheet_connector/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/google_sheet_connector/google_sheet_connector/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('google_sheet_connector.listing', {
#             'root': '/google_sheet_connector/google_sheet_connector',
#             'objects': http.request.env['google_sheet_connector.google_sheet_connector'].search([]),
#         })

#     @http.route('/google_sheet_connector/google_sheet_connector/objects/<model("google_sheet_connector.google_sheet_connector"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('google_sheet_connector.object', {
#             'object': obj
#         })
