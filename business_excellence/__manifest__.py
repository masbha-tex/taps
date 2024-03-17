# -*- coding: utf-8 -*-
{
    'name': "Business Excellence",
    'summary': """Business Excellence """,
    'description': """Long description of Business Excellence module's""",
    'author': "Mohammad Adnan",
    'category': 'Generic Modules/Business Excellence',
    'version': '0.1',

    'depends': ['base','mail','web'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/business_excellence.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    
    'qweb': [],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'images': ['static/src/img/icon.png'],
}
