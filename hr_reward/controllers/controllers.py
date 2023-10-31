# -*- coding: utf-8 -*-
# from odoo import http


# class HrReward(http.Controller):
#     @http.route('/hr_reward/hr_reward/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_reward/hr_reward/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_reward.listing', {
#             'root': '/hr_reward/hr_reward',
#             'objects': http.request.env['hr_reward.hr_reward'].search([]),
#         })

#     @http.route('/hr_reward/hr_reward/objects/<model("hr_reward.hr_reward"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_reward.object', {
#             'object': obj
#         })
