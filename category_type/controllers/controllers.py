# -*- coding: utf-8 -*-
# from odoo import http


# class CategTypeSetup(http.Controller):
#     @http.route('/categ_type_setup/categ_type_setup/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/categ_type_setup/categ_type_setup/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('categ_type_setup.listing', {
#             'root': '/categ_type_setup/categ_type_setup',
#             'objects': http.request.env['categ_type_setup.categ_type_setup'].search([]),
#         })

#     @http.route('/categ_type_setup/categ_type_setup/objects/<model("categ_type_setup.categ_type_setup"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('categ_type_setup.object', {
#             'object': obj
#         })
