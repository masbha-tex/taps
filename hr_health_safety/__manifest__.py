# -*- coding: utf-8 -*-
{
    'name': "Health & Safety",
    'summary': """Health & Safety""",
    'description': """Long description of Health & Safety module""",
    'author': "Mohammad Adnan",
    'category': 'Generic Modules/Health Safety',
    'version': '0.1',
    'depends': ['base','mail','web','hr','taps_hr'],

    
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/hs.xml',
        'views/templates.xml',
    ],
    
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'qweb': [],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'images': ['static/src/img/icon.png'],
}
