# -*- coding: utf-8 -*-
{
    'name': "taps_quality",

    'summary': """
        Quality Variants""",

    'description': """
        Check the quality of goods with all the attributes of testing
    """,

    'author': "Ashraful",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Quality',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','web_studio','stock','quality'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/quality_line.xml',
        'views/parameter.xml',
        'views/quality_unit.xml',
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}
