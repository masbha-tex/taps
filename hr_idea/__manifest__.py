# -*- coding: utf-8 -*-
{
    'name': "Idea Box",
    'summary': """Reward and Recognition Managment""",
    'author': "Reazul",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/Reward and Recognition',
    'version': '0.1',
    'description': '',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','hr','taps_hr','web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
