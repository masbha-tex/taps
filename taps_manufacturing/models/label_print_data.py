import json
import datetime
import math
import operator as py_operator
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import format_date


class labelPrintData(models.Model):
    _name = "label.print.data"
    _description = "Label Print Data"
    _check_company_auto = True
    
    name = fields.Char(string='Code', store=True)
    batch_lot = fields.Char(string='Batch / Lot', store=True)
    table_name = fields.Char(string='Table', store=True)
    qc_by = fields.Char(string='QC By', store=True)
    pre_check_by = fields.Char(string='Pre Check By', store=True)
    print_by = fields.Char(string='Print By', store=True)
    label_qty = fields.Char(string='Label Qty', store=True)
    label_copy = fields.Char(string='Copied', store=True)

    
    # oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    # company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    # oa_id = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)
    # oa_id = fields.Many2one('sale.order', string='OA', store=True)

    # def unlink(self):
    #     return super(labelPrintData, self).unlink()