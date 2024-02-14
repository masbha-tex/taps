# -*- coding: utf-8 -*-
{
    'name': "taps_crm",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Asraful",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/CRM',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','crm','taps_sale','whatsapp_mail_messaging','web_domain_field'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        'views/crm_views.xml',
        'views/visit_template_views.xml',
        'views/assets.xml',
        'views/crm_team_view.xml',
        'views/custom_chart_view.xml',
        'views/google_chart_view.xml',
        'views/saleperson_wise_customer_view.xml',
        'views/approval_matrix.xml',
        'views/customer_reallocation.xml',
        'views/brand_reallocation.xml',
        'views/crm_team_transfer.xml',
        'views/activity.xml',
        # 'views/provisional_naf.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [
        "static/src/xml/visit_dashboard.xml",
        "static/src/xml/custom_chart/custom_chart.xml",
        "static/src/xml/google_chart/google_chart.xml"
    ],
}
