# -*- coding: utf-8 -*-
{
    'name': "Taps HR",
    'summary': """Customization for HR Employee, HR Attendance""",

    'description': """This module integrates Odoo with the hr, employee, attendance""",

    'author': "Mohammad Adnan",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/Human Resources',
    "version": "14.0.1.0.0",
    "license": "OEEL-1",
    'depends': ['base_setup', 'hr_attendance', 'web_studio','hr','hr_payroll_account',],
    # always loaded
    'data': [
        'data/employee_id_generate.xml',
        'data/attendance_date_generate.xml',
        'data/attendance_flag_generate.xml',
        'data/overtime_calculate.xml',
        'views/attendance_views.xml',
        'views/employee_views.xml',
        'views/contract_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
