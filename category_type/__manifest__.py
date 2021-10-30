# -*- coding: utf-8 -*-
{
    'name': "Type of Category",

    'summary': """Setup Type of Category""",

    'description': """Setup Type of Category""",

    'author': "Sayed",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
   'data': [
        'security/ir.model.access.csv',
        'views/categ_type.xml',
    ],
}
