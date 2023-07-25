# -*- coding: utf-8 -*-
from odoo import http


class TapsLms(http.Controller):
    @http.route('/taps_lms/lms_keepalive', auth='user', type='json')
    def lms_keepalive(self):
        request.httprequest.session.modified = True
        return {}    

    @http.route('/lms/courses/', auth='public')
    def display_subjects(self, **kw):
        # return "Hello World! Here are the available subjects"
        # return http.request.render('lms.subjects', {
        #     'subjects':
        #         ['Math', 'English', 'Programming', 'Operating System'],
        # })
        courses = http.request.env['lms.course'].search([('state', 'in', ('draft', 'in-progress', 'completed'))])
        return http.request.render('lms.courses', {
            'courses': courses,
        })

    @http.route('/lms/<model("lms.course"):course>/', auth='public')
    def display_course_detail(self, course):
        return http.request.render('lms.course_detail', {'course': course})

