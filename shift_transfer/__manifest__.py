# -*- coding: utf-8 -*-
{
    'name': "Shift Transfer",

    'author': "adnan-tex",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'version': '14.0.1.0.0',
    'summary': """Integrating Shift Time Transfer With HR Attendance""",
    'description': """This module integrates Odoo with the Shift Time Transfer,hr,attendance""",
    'category': 'Generic Modules',

    # any module necessary for this one to work correctly
    'depends': ['base','web_studio','hr','base_setup'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/shift_code_generate.xml',
        'views/shift_transfer.xml',
    ],
    # only loaded in demonstration mode
    'license': 'OEEL-1',
    'demo': [],
    'installable': True,
    'auto_install': True,
    'application': False,
}
