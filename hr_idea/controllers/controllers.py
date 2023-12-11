# -*- coding: utf-8 -*-
# from odoo import http


# class HrIdea(http.Controller):
#     @http.route('/hr_idea/hr_idea/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_idea/hr_idea/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_idea.listing', {
#             'root': '/hr_idea/hr_idea',
#             'objects': http.request.env['hr_idea.hr_idea'].search([]),
#         })

#     @http.route('/hr_idea/hr_idea/objects/<model("hr_idea.hr_idea"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_idea.object', {
#             'object': obj
#         })
