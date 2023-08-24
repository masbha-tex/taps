# -*- coding: utf-8 -*-
{
    'name': "Retention Matrix",

    'summary': """Created a new module for Retention Heat matrix""",

    'description': """
        It's for the Retention Heat map.
    """,

    'author': "Reazul",
    'website': "http://www.yourcompany.com",
    'category': 'Generic Modules/Retention Matrix',
    'version': '0.1',

    'depends': ['base','hr','taps_hr'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        
        'data/ir_sequence.xml',
        'views/assets.xml',
        # 'views/templates.xml',
        'views/retention_matrix.xml',
        # 'views/reporting.xml',
        'wizard/retention_wizard.xml',

        'reports/paperformat.xml',        
        'reports/report_action_menu.xml',
        'reports/retention_matrix_report.xml',
    ],
    'qweb': [
        "static/src/xml/retention_dashboard.xml",
    ],    
    'installable': True,
    'application': True,
}
