import json

from babel.dates import format_date
from datetime import date
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.release import version


class AllocatedCustomer(models.Model):
    _name = 'customer.allocated'
    _description = 'Allocated Customer'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "salesperson ASC, id DESC"
    _rec_name="salesperson"

    allocated_line = fields.One2many('customer.allocated.line', 'allocated_id', string='Allocated Line', copy=True)
    salesperson = fields.Many2one('res.users', domain=[('share', '=', False),('sale_team_id', '!=', False),('sale_team_id.name', '!=', "MARKETING")], string="Salesperson")
    image_field = fields.Image('Photo', related="salesperson.image_1920")
    team_id = fields.Many2one('crm.team', string= "Team", related="salesperson.sale_team_id")
    region_id = fields.Many2one('team.region', string= "Region", compute="_compute_region")
    team_leader_id = fields.Many2one('res.users', string= "Team Leader", related="team_id.user_id")
    # customers = fields.Many2many('res.partner', string="Customers", domain="[['customer_rank', '=', 1]]")
    number_of_customer = fields.Integer(string="Number Of Customer", compute='_count_customer')
    customer_count = fields.Integer(compute='_compute_customer_for_individuals', string='Customer count')
    pi_count = fields.Integer( string='PI count', compute='_compute_pi_for_individuals',)
    sa_count = fields.Integer( string='SA count', compute='_compute_sa_for_individuals')
    oa_count = fields.Integer( string='OA count', compute='_compute_oa_for_individuals')
    opportunity_count = fields.Integer( string='Opportunity count')
    meeting_count = fields.Integer( string='Meeting count')
    activity_count = fields.Integer( string='Activity count')
    customer_ids = fields.Many2many('customer.allocated.line', compute='_compute_customer_for_individuals', string='Customers', copy=False)
    pi_ids = fields.Many2many('sale.order', compute='_compute_pi_for_individuals', string='PI', copy=False)
    oa_ids = fields.Many2many('sale.order', compute='_compute_oa_for_individuals', string='OA', copy=False)
    sa_ids = fields.Many2many('sale.order', compute='_compute_sa_for_individuals', string='SA', copy=False)
    # visit_ids = fields.Many2many('crm.visit', compute='_compute_visit', string='Customers', copy=False)

    @api.depends('salesperson')
    def _compute_region(self):
        for record in self:
            region = self.env['team.region'].sudo().search([('id', '=', self.salesperson.sale_team_id.region.id)])
            record.write({'region_id':region})
    
    def _compute_customer_for_individuals(self):
        for order in self:
            customer = order.env['customer.allocated.line'].sudo().search([('allocated_id', '=', self.id)])
            order.customer_ids = customer
            # raise UserError((len(ccr)))
            order.customer_count = len(customer)
            
    def _compute_pi_for_individuals(self):
        for record in self:
            pi = record.env['sale.order'].sudo().search([('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'sale')])
            record.pi_ids = pi
            # raise UserError((len(ccr)))
            record.pi_count = len(pi)
            
    def _compute_oa_for_individuals(self):
        for record in self:
            oa = record.env['sale.order'].sudo().search([('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'oa')])
            record.oa_ids = oa
            # raise UserError((len(ccr)))
            record.oa_count = len(oa)

    def _compute_sa_for_individuals(self):
        for record in self:
            sa = record.env['sale.order'].sudo().search([('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'sample')])
            record.sa_ids = sa
            # raise UserError((len(ccr)))
            record.sa_count = len(sa)
        

    def _count_customer(self):
        record = self.allocated_line
        count = 0
        for rec in record:
            count +=1
        self.number_of_customer = count
        
    def view_customer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Customers',
            'view_mode': 'tree',
            'res_model': 'customer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
            
        }
        
    def view_pi(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My PI',
            'view_mode': 'tree,form,kanban',
            'res_model': 'sale.order',
            'domain': [('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'sale')],
            'context': "{'create': False}"
        }
    def view_oa(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My OA',
            'view_mode': 'tree,form,kanban',
            'res_model': 'sale.order',
            'domain': [('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'oa')],
            'context': "{'create': False}"
        }
        
    def view_sample(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My SA',
            'view_mode': 'tree,form,kanban',
            'res_model': 'sale.order',
            'domain': [('user_id', '=', self.salesperson.id),('state', '=', 'sale'), ('sales_type', '=', 'sample')],
            'context': "{'create': False}"
        }
        
    def view_opportunity(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Customers',
            'view_mode': 'tree',
            'res_model': 'customer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
        }

    # def view_visit(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'My Customers',
    #         'view_mode': 'tree',
    #         'res_model': 'customer.allocated.line',
    #         'domain': [('allocated_id', '=', self.id)],
    #         'context': "{'create': False}"
    #     }
    def view_meeting(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'My Customers',
            'view_mode': 'tree',
            'res_model': 'customer.allocated.line',
            'domain': [('allocated_id', '=', self.id)],
            'context': "{'create': False}"
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


class AllocatedCustomerLine(models.Model):

    _name = 'customer.allocated.line'
    _description = 'Allocated Line'

    
        
    allocated_id = fields.Many2one('customer.allocated', string='Allocated Id', index=True, required=True, ondelete='cascade')
    name = fields.Char(string="Description")
    # domain = fields.Char()
    customer_domain = fields.Char(compute="_compute_customer",readonly=True, store=True)

    buyer = fields.Many2one('res.partner', string='Buyer', domain="[('buyer_rank', '=', 1)]" ,store=True, required=True)
    customer = fields.Many2one('res.partner', string='Customer',store=True, required=True)
    assign_date = fields.Date(string="Assign Date", default=date.today())
     
    
    
    

    
    @api.onchange('buyer')
    def _on_change_buyer(self):
        self.customer = False

    @api.depends('buyer')
    def _compute_customer(self):
        for rec in self:
           if self.buyer:
                  self.customer_domain = json.dumps([('id', 'in', self.buyer.related_customer.ids)])
           else:
               self.customer_domain = json.dumps([('id', '=', False)])



