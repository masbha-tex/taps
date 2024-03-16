{
    "name": "Taps Purchase",
    # Explain the purpose of the module
    "summary": """
        Show the last approver of the purchase on view
        """,
    'category': 'Generic Modules/Purchase',
    "version": "14.0.1.0.1",
    "author": "Odoo PS",
    "website": "http://www.odoo.com",
    "license": "OEEL-1",
    # Check depends order uncomment if necessary
    "depends": [
        'purchase',
        'web_studio',
    ],
    # Check data order
    "data": [
        "security/ir.model.access.csv",
        "views/purchase_order.xml",
        "views/purchase_req.xml",
        "views/purchase_approval_duration.xml",
    ],
    'qweb': [
        "static/src/xml/purchase_dashboard.xml",
    ],
    # Only used to link to the analysis / Ps-tech store
    "task_id": [2581117],
}
