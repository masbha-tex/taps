# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'Payroll - Attendance',
    'version': '1.0',
    'category': 'Human Resources/Payroll',
    'summary': 'Manage payslip ',
    'description': "Generate payslip worked hours based on employee attendance",
    'depends': ['hr_payroll', 'hr_attendance', 'hr_payroll_edit_lines'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_payroll_structure_views.xml',
        'views/hr_overtime_views.xml',
        'data/hr_payroll_planning_data.xml',
        'wizard/hr_work_entry_regeneration_wizard_views.xml',
    ],
    'installable': True,
    'auto_install': True,
}
