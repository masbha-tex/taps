# -*- coding: utf-8 -*-
{
    'name': "Inventory Valuation",

    'summary': """
        Report modification""",

    'description': """
        This model is for all the modification in inventory module.
    """,

    'author': "Sayed",
    'website': "http://www.odoo.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Inventory',
    'version': '14.0.1.0.0',
    "license": "OEEL-1",

    # any module necessary for this one to work correctly
    'depends': ['base_setup', 'stock', 'account', 'web_studio'],

    # always loaded
    
    'data': [
        #'data/insert_schedule_date.xml',
        'views/stock_register_views.xml',
        'views/product_template.xml',
        'views/product_move.xml',
        #'security/stock_account_security.xml',
        #'security/ir.model.access.csv',
        #'wizard/stock_valuation_layer_revaluation_views.xml',
        #'report/report_stock_forecasted.xml',
    ],
}
