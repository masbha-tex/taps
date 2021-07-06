{
    "name": "Purchase Last Approver",
    # Explain the purpose of the module
    "summary": """
        Show the last approver of the purchase on view
        """,
    "category": "",
    "version": "14.0.1.0.0",
    "author": "Odoo PS",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    # Check depends order uncomment if necessary
    "depends": [
        'purchase',
    ],
    # Check data order
    "data": [
        "views/purchase_order.xml",
    ],
    # Only used to link to the analysis / Ps-tech store
    "task_id": [2581117],
}
