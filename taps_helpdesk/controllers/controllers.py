# -*- coding: utf-8 -*-
# from odoo import http


# class TapsHelpdesk(http.Controller):
#     @http.route('/taps_helpdesk/taps_helpdesk/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_helpdesk/taps_helpdesk/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_helpdesk.listing', {
#             'root': '/taps_helpdesk/taps_helpdesk',
#             'objects': http.request.env['taps_helpdesk.taps_helpdesk'].search([]),
#         })

#     @http.route('/taps_helpdesk/taps_helpdesk/objects/<model("taps_helpdesk.taps_helpdesk"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_helpdesk.object', {
#             'object': obj
#         })
