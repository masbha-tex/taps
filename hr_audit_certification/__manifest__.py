# -*- coding: utf-8 -*-
{
    'name': "Audit & Certification",
    'summary': """Audit & Certification""",
    'description': """Long description of module's purpose """,
    'author': "My Company",
    'category': 'Generic Modules/Audit Certification',
    'version': '0.1',

    'depends': ['base','mail','web','hr','taps_hr'],

    # always loaded
    'data': [
        'security/res_groups.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence.xml',
        'views/audit_certification.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
    'qweb': [],    
    'license': 'AGPL-3',
    'installable': True,
    'application': True,
    'images': ['static/src/img/icon.png'],
}
