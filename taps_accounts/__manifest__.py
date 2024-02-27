# -*- coding: utf-8 -*-
{
    'name': "taps_accounts",

    'summary': """
        Modified Accounts""",

    'description': """
        Required addition and modification on Accounts
    """,

    'author': "Tex Zippers (BD) Limited.",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Accounts',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['account','taps_inventory','taps_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/accounts_budget.xml',
        'views/combine_invoice_view.xml'
    ],
    # only loaded in demonstration mode
    #'demo': [
    #    'demo/demo.xml',
    #],
}
