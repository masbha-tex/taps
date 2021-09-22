# -*- coding: utf-8 -*-
{
    'name': "Attendance Job Card",
    'summary': """Integrating Shift time With HR Attendance""",

    'description': """This module integrates Odoo with the hr,attendance""",

    'author': "Mohammad Adnan",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/Human Resources',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    "version": "14.0.1.0.0",
    "license": "OEEL-1",

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'hr_attendance', 'web_studio',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
}
