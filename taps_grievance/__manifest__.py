# -*- coding: utf-8 -*-
{
    'name': "taps_grievance",
    'summary': """Grievance management""",
    'author': "Mohammad Adnan",
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
        'views/views.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
