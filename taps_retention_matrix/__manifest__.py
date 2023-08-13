# -*- coding: utf-8 -*-
{
    'name': "taps_retention_matrix",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Reazul",
    'website': "http://www.yourcompany.com",
    'category': 'Generic Modules/Retention Matrix',
    'version': '0.1',

    'depends': ['base','hr','taps_hr'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
        'views/retention_matrix.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
