# -*- coding: utf-8 -*-
{
    'name': "LMS",
    'summary': """Manage trainings""",
    'author': "Mohammad Adnan",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/LMS',
    'version': '0.1',
    'description': """
        LMS module for managing trainings:
            - training courses
            - training sessions
            - attendees registration
    """,
    # any module necessary for this one to work correctly
    'depends': ['base', 'mail', 'report_xlsx'],

    # always loaded
    'data': [
        'data/activity.xml',
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'views/lms.xml',
        'views/res_partner.xml',
        'reports/custom_header_footer.xml',
        'reports/paperformat.xml',
        'reports/reports.xml',
        'data/email_template.xml',
        'data/ir_cron.xml',
        'data/ir_sequence.xml',
        'views/res_config_settings.xml',
        'wizard/report_wizard_view.xml',
        'reports/lms_pdf_report.xml',
        'reports/lms_xlsx_report.xml',
        'views/template.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
    ],
    'images': ['static/img/success.png'],
    'installable': True,
    'application': True,
}
