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
    'depends': ['base_setup', 'stock', 'account', 'web_studio','base', 'web', 'stock_account', 'product'],

    # always loaded
    
    'data': [
        #'data/insert_schedule_date.xml',
        #'data/update_duration_for_ageing.xml',
        "views/stock_quant.xml",
        'data/create_update_qc.xml',
        'reports/sample_print_out_pdf.xml',
        'reports/report_action.xml',
        'views/assets.xml',
        'views/stock_register_views.xml',
        'views/product_template.xml',
        'views/product_move.xml',
        'views/ageing.xml',
        'views/stock_opening_closing.xml',
        'views/fg_category.xml',
        'security/ir.model.access.csv',
        #'wizard/stock_valuation_layer_revaluation_views.xml',
        #'report/report_stock_forecasted.xml',
    ],
    'css': ['static/src/css/custom_styles.css'],
}
