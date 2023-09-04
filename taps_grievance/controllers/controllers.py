# -*- coding: utf-8 -*-
# from odoo import http


# class TapsGrievance(http.Controller):
#     @http.route('/taps_grievance/taps_grievance/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/taps_grievance/taps_grievance/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('taps_grievance.listing', {
#             'root': '/taps_grievance/taps_grievance',
#             'objects': http.request.env['taps_grievance.taps_grievance'].search([]),
#         })

#     @http.route('/taps_grievance/taps_grievance/objects/<model("taps_grievance.taps_grievance"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('taps_grievance.object', {
#             'object': obj
#         })
