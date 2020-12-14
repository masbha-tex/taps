# -*- coding: utf-8 -*-
{
    'name': "taps customization",

    'summary': "Odoo Customization",

    'author': "Odoo FJA",
    'version': '0.1',
    'depends': ['hr_payroll', 'hr_attendance'],

    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        #'data/overtime_rule.xml'
    ],
}
