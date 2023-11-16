# -*- coding: utf-8 -*-
{
    'name': "Taps Web",
    'summary': """Web Manage""",
    'description': """App for Web Module inherit and Manage some functional term""",
    'author': "My Company",
    'category': 'Generic Modules/Web',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','web'],

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
    'qweb': [
        
    ],
}
