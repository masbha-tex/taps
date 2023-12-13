# -*- coding: utf-8 -*-
{
    'name': "Idea Box",
    'summary': """Idea Share Managment""",
    'author': "Reazul",
    # 'website': "http://www.odoo.com",
    'category': 'Generic Modules/Idea Box',
    'version': '0.1',
    'description': '',

    # any module necessary for this one to work correctly
    'depends': ['base','mail','hr','taps_hr','web'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/views.xml',
        'views/idea_email_matrix_views.xml',
        'views/idea_criteria_views.xml',
        # 'views/idea_title_views.xml',
        'views/templates.xml',
    ],
    'qweb': [],      
    'images': [],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
}
