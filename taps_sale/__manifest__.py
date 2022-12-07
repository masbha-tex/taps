# -*- coding: utf-8 -*-
{
    'name': "taps_sale",

    'summary': """Split Description""",

    'description': """
        This is for spliting the attributes of product into different column of table
    """,

    'author': "Texzipper",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Sales',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','stock', 'web_studio'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/sale.xml',
        'views/buyer_name.xml',
        'views/sale_overview.xml',
        'views/mrp_productivity.xml',
        'reports/report_action.xml',
        'reports/report_proforma_invoice.xml',
        'reports/report_oa_invoice.xml',
        'reports/paperformat.xml',
        #'data/ir_oa_sequance.xml',
        #'views/fg_product.xml',
    ],
    # only loaded in demonstration mode
}
