# -*- coding: utf-8 -*-

from odoo import models, fields, api


class OrganizationalChart(models.Model):
    _name = 'hr.organizational.chart'
    _description = "HR Organizational Chart"

    @api.model
    def get_employee_data(self, emp_id):
        parent_emp = self.env['hr.employee'].search([('id', '=', str(emp_id))])
        data = {
            'name': parent_emp.name,
            'title': self._get_position(parent_emp),
            'children': [],
            'office': self._get_image(parent_emp),
        }
        employees = self.env['hr.employee'].search([('parent_id', '=', parent_emp.id)])
        for employee in employees:
            data['children'].append(self.get_children(employee, 'middle-level'))

        return {'values': data}

    @api.model
    def get_children(self, emp, style=False):
        data = []
        emp_data = {'name': emp.name, 'title': self._get_position(emp), 'office': self._get_image(emp)}
        childrens = self.env['hr.employee'].search([('parent_id', '=', emp.id)])
        for child in childrens:
            sub_child = self.env['hr.employee'].search([('parent_id', '=', child.id)])
            next_style = self._get_style(style)
            if not sub_child:
                data.append({'name': child.name, 'title': self._get_position(child), 'className': next_style,
                             'office': self._get_image(child)})
            else:
                data.append(self.get_children(child, next_style))

        if childrens:
            emp_data['children'] = data
        if style:
            emp_data['className'] = style

        return emp_data

    def _get_style(self, last_style):
        if last_style == 'middle-level':
            return 'product-dept'
        if last_style == 'product-dept':
            return 'rd-dept'
        if last_style == 'rd-dept':
            return 'pipeline1'
        if last_style == 'pipeline1':
            return 'frontend1'

        return 'middle-level'

    def _get_image(self, emp):
        image_path = """<img src='/web/image/hr.employee.public/""" + str(emp.id) + """/image_1024/' id='""" + str(
            emp.id) + """'/>"""
        return image_path

    def _get_position(self, emp):
        if emp.sudo().job_id:
            return emp.sudo().job_id.name
        return ""

    
    def _get_department(self, department_id):
        if department.sudo().depertment_id:
            return department.sudo().department_id.department_name
        return ""
    
    @api.depends('department_id')
    def _compute_parent_id(self):
        for employee in self.filtered('department_id.manager_id'):
            employee.parent_id = employee.department_id.manager_id