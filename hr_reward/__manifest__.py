# -*- coding: utf-8 -*-
{
    'name': "Reward and Recognition",
    'summary': """Reward and Recognition Managment""",
    'author': "Reazul",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/Grievance',
    'version': '0.1',
    'description': '',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','hr',],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        # 'views/assets.xml',
        'views/views.xml',
        'views/matrix_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
