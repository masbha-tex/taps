# -*- coding: utf-8 -*-

{
    'name': 'Payroll - Attendance',
    'summary': 'Generate payslip worked hours based on employee attendance and overtime',
    'version': '14.0.1.0',
    'category': 'Human Resources/Payroll',
    'depends': ['hr_payroll', 'hr_attendance', 'hr_payroll_edit_lines'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_overtime_views.xml',
        'data/hr_payroll_planning_data.xml',
        'wizard/hr_work_entry_regeneration_wizard_views.xml',
    ],
    'installable': False,
    'auto_install': False,
}
