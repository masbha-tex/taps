# -*- coding: utf-8 -*-
{
    'name': "taps_expense",

    'summary': """
        For rename 'company' to 'Expense to Vendor' in selection method""",

    'description': """
        This model is used for full fill the required things about expense module.
    """,

    'author': "GS RABBANI",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','hr_expense'],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_expense.xml',
        'views/hr_emp_imprest.xml',
        'data/generate_expense_code.xml',
        'data/generate_imprest_code.xml',
    ],
}
