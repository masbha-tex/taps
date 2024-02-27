import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class AllocatedBuyer(models.Model):
    _name = 'buyer.allocated'
    _description = 'Allocated Buyer'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "marketingperson ASC, id DESC"
    _rec_name="marketingperson"

    allocated_line = fields.One2many('buyer.allocated.line', 'allocated_id', string='Allocated Line', copy=True)
    marketingperson = fields.Many2one('res.users', domain=[('share', '=', False),('sale_team_id', '!=', False),('sale_team_id.name', '=', "MARKETING")], string="Marketing Person")
    team_id = fields.Many2one('crm.team', string= "Team", related="marketingperson.sale_team_id")
    # customers = fields.Many2many('res.partner', string="Customers", domain="[['customer_rank', '=', 1]]")
    number_of_buyer = fields.Integer(string="Number Of Buyer", compute='_count_buyer')

    def _count_buyer(self):
        record = self.allocated_line
        count = 0
        for rec in record:
            count +=1
        self.number_of_buyer = count


class AllocatedBuyerLine(models.Model):

    _name = 'buyer.allocated.line'
    _description = 'Buyer Allocated Line'

    
        
    allocated_id = fields.Many2one('buyer.allocated', string='Allocated Line', index=True, required=True, ondelete='cascade')
    name = fields.Char(string="Description")
    # domain = fields.Char()
    # customer_domain = fields.Char(compute="_compute_buyer",readonly=True, store=True)

    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]" ,store=True, required=True)
    # customer = fields.Many2one('res.partner', string='Customer',store=True, required=True)
    assign_date = fields.Date(string="Assign Date", default=date.today())
     
    
    
    

    


