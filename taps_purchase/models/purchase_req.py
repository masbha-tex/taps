from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import formatLang, get_lang, format_amount

class PurchaseReq(models.Model):
    _inherit = "approval.request"
    #_order = 'priority desc, id desc'
    
    priority = fields.Selection(
        [('0', 'Normal'), ('1', 'Urgent')], 'Priority', default='0', index=True)