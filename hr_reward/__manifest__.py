# -*- coding: utf-8 -*-
{
    'name': "R & R",
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
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'data/template_hod.xml',
        # 'views/assets.xml',
        'views/views.xml',
        'views/matrix_views.xml',
        'views/reward_criteria_views.xml',
        'views/reward_title_views.xml',
        'views/templates.xml',
    ],
    'qweb': [],      
    'images': ['static/src/img/rr.png'],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
