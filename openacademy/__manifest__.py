{
    'name': "LMS",

    'summary': """Manage trainings""",

    'description': """
        LMS module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,

    'author': "Mohammad Adnan",
    'website': "http://www.odoo.com",


    'category': 'Generic Modules/Human Resources',
    "version": "14.0.1.0.1",

    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'sale', 'report_xlsx'],

    # always loaded
    'data': [
        'data/activity.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/openacademy.xml',
        'views/res_partner.xml',
        'reports/custom_header_footer.xml',
        'reports/paperformat.xml',
        'reports/reports.xml',
        'data/email_template.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'reports/sale_qweb_template.xml',
        'views/res_config_settings.xml',
        'wizard/report_wizard_view.xml',
        'reports/openacademy_pdf_report.xml',
        'reports/openacademy_xlsx_report.xml',
        'views/product_sale_analysis.xml',
        'views/template.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images': ['static/img/success.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
