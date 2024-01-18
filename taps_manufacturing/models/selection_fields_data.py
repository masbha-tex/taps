import json
import datetime
import math
import operator as py_operator
import re

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.misc import format_date


class SelectionFieldsData(models.Model):
    _name = "selection.fields.data"
    _description = "Selection Fields Data"
    _check_company_auto = True
    
    field_name = fields.Char(string='Field Name', store=True)
    name = fields.Char(string='Field Value', store=True)
    # oa_id = fields.Many2one('sale.order', string='OA', store=True, readonly=True)
    # company_id = fields.Many2one('res.company', index=True, default=lambda self: self.env.company, string='Company', readonly=True)
    # oa_id = fields.Many2one('sale.order', string='OA', store=True, domain="['|','&', ('company_id', '=', False), ('company_id', '=', company_id), ('sales_type', '=', 'oa'), ('state', '=', 'sale')]", check_company=True)
    # oa_id = fields.Many2one('sale.order', string='OA', store=True)

    def unlink(self):
        return super(SelectionFieldsData, self).unlink()