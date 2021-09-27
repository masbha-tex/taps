# -*- coding: utf-8 -*-
# from odoo import http


# class ShiftTransfer(http.Controller):
#     @http.route('/shift_transfer/shift_transfer/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/shift_transfer/shift_transfer/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('shift_transfer.listing', {
#             'root': '/shift_transfer/shift_transfer',
#             'objects': http.request.env['shift_transfer.shift_transfer'].search([]),
#         })

#     @http.route('/shift_transfer/shift_transfer/objects/<model("shift_transfer.shift_transfer"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('shift_transfer.object', {
#             'object': obj
#         })
