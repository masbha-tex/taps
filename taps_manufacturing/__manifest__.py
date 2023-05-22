# -*- coding: utf-8 -*-
{
    'name': "taps_manufacturing",

    'summary': """
        Customized Manufacturing""",

    'description': """
        To full fill all the porupose of manufacturing process
    """,

    'author': "Texzipper",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Manufacturing',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','web_studio','product', 'stock', 'resource','sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/mrp_productivity.xml',
        'views/mrp_production.xml',
        'views/mrp_workorder.xml',
        #'wizard/manufacturing_report_wizard.xml'
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
