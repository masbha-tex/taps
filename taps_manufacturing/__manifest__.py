# -*- coding: utf-8 -*-
{
    'name': "taps_manufacturing",

    'summary': """
        Customized Manufacturing""",

    'description': """
        To full fill all the porupose of manufacturing process
    """,

    'author': "Texzipper",
    'website': "http://www.texfasteners.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Generic Modules/Manufacturing',
    'version': '14.0.1.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base','web','web_studio','product', 'stock', 'resource','sale','mrp', 'barcodes','report_xlsx','taps_sale'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        # 'report/mrp_lot_barcode.xml',
        'wizard/mrp_split.xml',
        'wizard/bom_verification.xml',
        'wizard/mrp_plan.xml',
        'wizard/mrp_lot.xml',
        'wizard/mrp_sizewise_lot.xml',
        'wizard/requisition.xml',
        'wizard/mrp_output.xml',
        'wizard/mrp_qc_output.xml',
        'wizard/mrp_delivery.xml',
        'wizard/mrp_group_output.xml',
        'views/assets.xml',
        'views/mrp_productivity.xml',
        'views/mrp_production.xml',
        'views/mrp_workorder.xml',
        'views/manufacturing.xml',
        'views/operation_details.xml',
        'views/mrp_workcenter.xml',
        'views/machine_list.xml',
        'views/packing_report_view.xml',
        'data/ir_lot_sequence.xml',
        'report/report_action.xml',
        'report/mrp_lot_barcode.xml',
        'report/mrp_rpt_wizard.xml',
        # 'wizard/manufacturing_report_wizard.xml'
    ],
    'qweb': [
        "static/src/xml/qweb_templates.xml",
    ],
    
    'license': 'LGPL-3',
    # only loaded in demonstration mode
    # 'demo': [
    #     'demo/demo.xml',
    # ],
}
