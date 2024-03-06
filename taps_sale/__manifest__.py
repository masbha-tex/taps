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

    # any module necessary for this one to work correctly taps_manufacturing
    'depends':['base','sale','stock','web_studio','web','report_xlsx','account','crm'],

    # always loaded
    'data': [
        'views/assets.xml',
        'security/ir.model.access.csv',
        'reports/paperformat.xml',
        'views/sale_representative.xml',
        'views/provisional_naf.xml',
        'views/sale.xml',
        'views/buyer_name.xml',
        'views/sale_overview.xml',
        #'views/mrp_productivity.xml',
        
        'views/team_wise_target.xml',
        'views/sale_ccr_view.xml',
        'views/sale_ccr_view_old.xml',
        'views/naf_template_view.xml',
        
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
        # 'data/ir_ccr_sequence.xml',
        'data/send_oa_to_respective_persons.xml',
        'data/daily_oa_release_email.xml',
        'data/oa_release_team_wise.xml',
        'data/oa_release.xml',
        'data/oa_release_mt.xml',
        'data/oa_release_body.xml',
        'data/oa_release_body_team_wise.xml',
        'data/mail_data_ccr.xml',
        # 'views/assets.xml',
        'views/variant_templates.xml',
        'views/action_reporting_dashboard.xml',
        'reports/report.xml',
        'views/order_flow.xml',
        'views/sale_order_rmc.xml',
        'wizard/sales_report_wizard.xml',
        'wizard/oa_update_confirm.xml',
        'wizard/ccr_wizard.xml',
        'wizard/order_modification_warning.xml',
        'views/activity.xml',
        'views/approval_matrix.xml',
        'views/allocated_customer_view.xml',
        'views/allocated_buyer_view.xml',
        'views/customer_reallocation.xml',
        'views/brand_reallocation.xml',
        
    ],
    'qweb': ["static/src/xml/sale_dashboard.xml",
             "static/src/xml/sale_reporting_dashboard.xml",
             "static/src/ccr/ccr_dashboard.xml",
             # "static/src/xml/similar_customer.xml",
             # "static/src/xml/confirmation_box.xml",
            ],
    # only loaded in demonstration mode
    'installable': True,
    'auto_install': False,
    'application': True,
}
