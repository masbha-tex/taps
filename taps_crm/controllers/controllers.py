# -*- coding: utf-8 -*-
# from odoo import http


# class TapsCrm(http.Controller):
#     @http.route('/taps_crm/taps_crm/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_crm/taps_crm/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_crm.listing', {
#             'root': '/taps_crm/taps_crm',
#             'objects': http.request.env['taps_crm.taps_crm'].search([]),
#         })

#     @http.route('/taps_crm/taps_crm/objects/<model("taps_crm.taps_crm"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_crm.object', {
#             'object': obj
#         })
