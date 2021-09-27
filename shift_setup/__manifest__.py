# -*- coding: utf-8 -*-
{
    'name': "Shift Setup",

    'author': "adnan-tex",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'version': '14.0.1.0.0',
    'license': 'OEEL-1',
    'summary': """Integrating Shift Time Setup With HR Attendance""",
    'description': """This module integrates Odoo with the Shift Time Setup,hr,attendance""",
    'category': 'Generic Modules/Human Resources',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/shift_setup.xml',
    ],
    # only loaded in demonstration mode
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': False,
}
}
