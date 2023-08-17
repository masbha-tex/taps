# -*- coding: utf-8 -*-
{
    'name': "taps_retention_matrix",

    'summary': """Create new module for Retention Heat matrix""",

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
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/retention_matrix.xml',
    ],
    'installable': True,
    'application': True,
}
