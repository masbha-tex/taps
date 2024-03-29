{
    "name": "Inventory New Columns",
    # Explain the purpose of the module
    "summary": """
        Inventory New Columns scaffold module
        """,
    'category': 'Generic Modules/Inventory New Columns',
    "version": "14.0.1.0.0",
    "author": "Odoo PS",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    # Check depends order uncomment if necessary
    "depends": [
        'product',
        'stock',
        'stock_account',
    ],
    # Check data order
    "data": [
        "views/stock_quant.xml",
    ],
    # Only used to link to the analysis / Ps-tech store
    "task_id": [2523902],
}
