# -*- coding: utf-8 -*-
# from odoo import http


# class HrAuditCertification(http.Controller):
#     @http.route('/hr_audit_certification/hr_audit_certification/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/hr_audit_certification/hr_audit_certification/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('hr_audit_certification.listing', {
#             'root': '/hr_audit_certification/hr_audit_certification',
#             'objects': http.request.env['hr_audit_certification.hr_audit_certification'].search([]),
#         })

#     @http.route('/hr_audit_certification/hr_audit_certification/objects/<model("hr_audit_certification.hr_audit_certification"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('hr_audit_certification.object', {
#             'object': obj
#         })
