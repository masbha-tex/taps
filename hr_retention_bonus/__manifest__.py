# -*- coding: utf-8 -*-

{
    'name': 'Retention Bonus Scheme',
    'version': '14.0.1.0.0',
    'summary': 'Manage Retention Bonus Scheme',
    'description': """
        Helps you to manage Retention Bonus Scheme of your company's staff.
        """,
    'category': 'Generic Modules/Retention Bonus',
    'author': "Mohammad Adnan",
    'company': 'TEX',
    'maintainer': 'Adnan',
    'live_test_url': 'https://youtu.be/LdUvXDMkd4Q',
    'website': "https://taps.odoo.com",
    'depends': [
        'base', 'hr','hr_payroll'
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/hr_retention_bonus_seq.xml',
        'data/salary_rule_loan.xml',
        'data/retention_matrix_rule.xml',
        'data/reminder_payment.xml',
        'views/hr_retention_bonus.xml',
        'views/hr_retention_matrix_views.xml', 
        'reports/report_action.xml',
        'reports/report_retention_bonus.xml',
        'reports/template.xml',
        'reports/state_templates.xml',
        'wizard/retention_bonus_report_wizard.xml',
        
        #'views/hr_payroll.xml',
    ],
    'license': 'OPL-1',
    'installable': True,
    'auto_install': False,
    'application': False,
}
