# -*- coding: utf-8 -*-
{
    'name': "Business Excellence",
    'summary': """Business Excellence """,
    'description': """Long description of Business Excellence module's""",
    'author': "Mohammad Adnan",
    'category': 'Generic Modules/Business Excellence',
    'version': '0.1',

    'depends': ['base','mail','web','hr','taps_hr'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/business_excellence.xml',
        'views/be_criteria_views.xml',
        'views/be_title_views.xml',
        'views/be_area_impact_views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    
    'qweb': [],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'images': ['static/src/img/icon.png'],
}
