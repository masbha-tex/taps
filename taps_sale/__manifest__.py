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
    'depends': ['base','sale','stock', 'web_studio','sales_team','web','report_xlsx'],

    # always loaded
    'data': [
        'views/assets.xml',
        'security/ir.model.access.csv',
        'reports/paperformat.xml',
        'views/sale.xml',
        'views/buyer_name.xml',
        'views/sale_overview.xml',
        #'views/mrp_productivity.xml',
        'views/sale_representative.xml',
        # 'views/bank.xml',
        'reports/report_action.xml',
        'reports/report_proforma_invoice.xml',
        'reports/report_oa_invoice.xml',
        'reports/report_proforma_invoice_mt.xml',
        'reports/report_oa_invoice_mt.xml',
        'reports/report_sa_invoice.xml',
        'reports/report_sa_invoice_mt.xml',
        'reports/report_sa_submission_mt.xml',
        'data/ir_oa_sequence.xml',
        'data/send_oa_to_respective.xml',
        'data/send_oa_to_respective_persons.xml',
        'data/daily_oa_release_email.xml',
        'data/oa_release.xml',
        # 'data/mail_template_action.xml',
        #'views/fg_product.xml',
        # 'views/assets.xml',
        'views/variant_templates.xml',
        'reports/report.xml',
        'views/order_flow.xml',
        'wizard/sales_report_wizard.xml',
        
        
        
    ],
    'qweb': ["static/src/xml/sale_dashboard.xml"],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': True,
}
