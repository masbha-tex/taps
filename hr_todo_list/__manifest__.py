{
    'name': "To Do List",
    'summary': """
        Create Todo List Using Activities""",
    'description': """
        Scheduling Activities For each model  and General Activities.
            """,
    'author': "Mohammad Adnan",
    'website': "http://www.odoo.com",
    'category': 'Generic Modules/To Do List',
    'version': '0.1',

    'depends': ['base', 'mail'],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/recurring.xml',
        'data/general.xml',
        'views/views.xml',
    ],
    'license': 'LGPL-3',
    'images': ['static/description/banner.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
