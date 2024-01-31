import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version



class ReAllocation(models.Model):

    _name = 'reallocation.form'
    _description = 'Re-Allocation Form'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    type = fields.Selection([
        ('customer', 'Customer'),
        ('buyer', 'Buyer')
        
    ],string="Type", required=True)

    select_customer = fields.Many2many('res.partner', domain="[['customer_rank', '=', 1]]", string='Select Customer')
    existing_user = fields.Many2one('res.users', string="Sales/Marketing person", domain=[('share', '=', False) ])

    new_user = fields.Many2one('res.users', string=" Assigned Sales/Marketing person", domain=[('share', '=', False) ])

    is_removed = fields.Boolean('Select to remove the customer from previous person',default=False)







