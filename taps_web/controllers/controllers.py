# -*- coding: utf-8 -*-
# from odoo import http


# class TapsWeb(http.Controller):
#     @http.route('/taps_web/taps_web/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_web/taps_web/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_web.listing', {
#             'root': '/taps_web/taps_web',
#             'objects': http.request.env['taps_web.taps_web'].search([]),
#         })

#     @http.route('/taps_web/taps_web/objects/<model("taps_web.taps_web"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_web.object', {
#             'object': obj
#         })
