# -*- coding: utf-8 -*-
# from odoo import http


# class ShiftSetup(http.Controller):
#     @http.route('/shift_setup/shift_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/shift_setup/shift_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('shift_setup.listing', {
#             'root': '/shift_setup/shift_setup',
#             'objects': http.request.env['shift_setup.shift_setup'].search([]),
#         })

#     @http.route('/shift_setup/shift_setup/objects/<model("shift_setup.shift_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('shift_setup.object', {
#             'object': obj
#         })
