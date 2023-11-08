# -*- coding: utf-8 -*-
# from odoo import http


# class WhatsappGateway(http.Controller):
#     @http.route('/whatsapp_gateway/whatsapp_gateway/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/whatsapp_gateway/whatsapp_gateway/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('whatsapp_gateway.listing', {
#             'root': '/whatsapp_gateway/whatsapp_gateway',
#             'objects': http.request.env['whatsapp_gateway.whatsapp_gateway'].search([]),
#         })

#     @http.route('/whatsapp_gateway/whatsapp_gateway/objects/<model("whatsapp_gateway.whatsapp_gateway"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('whatsapp_gateway.object', {
#             'object': obj
#         })
