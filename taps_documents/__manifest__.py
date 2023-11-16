# -*- coding: utf-8 -*-
{
    'name': "Taps Documents",

    'summary': "Document management",

    'description': """
        App to upload and manage your documents.
    """,

    'author': "Mohammad Adnan",
    'category': 'Generic Modules/Documents',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','documents','web'],

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
