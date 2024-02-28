# -*- coding: utf-8 -*-
# from odoo import http


# class HrHealthSafety(http.Controller):
#     @http.route('/hr_health_safety/hr_health_safety/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_health_safety/hr_health_safety/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_health_safety.listing', {
#             'root': '/hr_health_safety/hr_health_safety',
#             'objects': http.request.env['hr_health_safety.hr_health_safety'].search([]),
#         })

#     @http.route('/hr_health_safety/hr_health_safety/objects/<model("hr_health_safety.hr_health_safety"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_health_safety.object', {
#             'object': obj
#         })
