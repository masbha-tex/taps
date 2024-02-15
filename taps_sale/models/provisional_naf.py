from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class ProvisionalNaf(models.Model):
    _name = 'provisional.template'
    _description = 'Provisional Naf'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "name ASC, id DESC"
    _rec_name="name"


    type = fields.Selection([
        ('customer', 'Customer'),
        ('buyer', 'Buyer'),
        ('buyinghouse', 'Buying House'),
        
    ],string="Type", required=True)

    name = fields.Char(index=True, string="Name", required=True)
    # visit_id = fields.Many2one('crm.visit','Visit')
    

    
    
    
    
