# -*- coding: utf-8 -*-
{
    'name': "Item Typewise Purchase",

    'summary': """
        In Purchase Should Have Item Type""",

    'description': """
        This module is for adding an external field to the purchase module
    """,

    
    "category": "",
    "version": "14.0.1.0.0",
    "author": "Sayed",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    # Check depends order uncomment if necessary
    "depends": [
        'purchase',
        'web_studio',
    ],
    # Check data order
    "data": [
        "views/purchase_itemtype.xml",
    ],
}
