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
    image_field = fields.Image('Photo', related="marketingperson.image_1920")
    team_id = fields.Many2one('crm.team', string= "Team", related="marketingperson.sale_team_id")
    # customers = fields.Many2many('res.partner', string="Customers", domain="[['customer_rank', '=', 1]]")
    number_of_buyer = fields.Integer(string="Number Of Buyer", compute='_count_buyer')
    opportunity_count = fields.Integer( string='Opportunity count')
    buyer_count = fields.Integer(compute='_compute_buyer_for_individuals', string='Buyer count')
    meeting_count = fields.Integer( string='Meeting count')
    activity_count = fields.Integer( string='Activity count')
    meeting_ids = fields.Many2many('calendar.event', string="Meeting")
    buyer_ids = fields.Many2many('buyer.allocated.line', compute='_compute_buyer_for_individuals', string='Customers', copy=False)
    active = fields.Boolean(string="Active", default="True")

    def _count_buyer(self):
        record = self.allocated_line
        count = 0
        for rec in record:
            count +=1
        self.number_of_buyer = count

    def _compute_buyer_for_individuals(self):
        for order in self:
            buyer = order.env['buyer.allocated.line'].sudo().search([('allocated_id', '=', self.id)])
            order.buyer_ids = buyer
            # raise UserError((len(ccr)))
            order.buyer_count = len(buyer)
    
            
    def view_buyer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My buyers',
            'view_mode': 'tree,kanban',
            'res_model': 'buyer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
            
        }
    def view_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Opportunity',
            'view_mode': 'tree',
            'res_model': 'buyer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
        }

    def view_meeting(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Meeting',
            'view_mode': 'tree',
            'res_model': 'buyer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': True}"
        }
        
    def view_activity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Activity',
            'view_mode': 'tree',
            'res_model': 'customer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
        }


class AllocatedBuyerLine(models.Model):

    _name = 'buyer.allocated.line'
    _description = 'Buyer Allocated Line'

    
        
    allocated_id = fields.Many2one('buyer.allocated', string='Allocated Line', index=True, required=True, )
    name = fields.Char(string="Description")
    # domain = fields.Char()
    # customer_domain = fields.Char(compute="_compute_buyer",readonly=True, store=True)

    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]" ,store=True, required=True)
    # customer = fields.Many2one('res.partner', string='Customer',store=True, required=True)
    assign_date = fields.Date(string="Assign Date", default=date.today())
    active = fields.Boolean(string="Active", default="True")
     
    
    
    

    


