import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerAllocation(models.Model):
    _name = 'customer.allocation'
    _description = 'Salesperson Wise Customer'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "salesperson ASC, id DESC"
    _rec_name="salesperson"

    salesperson = fields.Many2one('res.users', domain=[('share', '=', False),('sale_team_id', '!=', False)], string="Salesperson")
    team_id = fields.Many2one('crm.team', string= "Team", related="salesperson.sale_team_id")
    customers = fields.Many2many('res.partner', string="Customers", domain="[['customer_rank', '=', 1]]")


class BrandAllocation(models.Model):
    _name = 'brand.allocation'
    _description = 'Marketingperson Wise Brand'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = "marketing_person ASC, id DESC"
    _rec_name="marketing_person"

    marketing_person = fields.Many2one('res.users', domain=[('share', '=', False),('sale_team_id.name', '=', 'MARKETING') ], string="Markting Person")
    team_id = fields.Many2one('crm.team', string= "Team", related="marketing_person.sale_team_id")
    brand = fields.Many2many('res.partner', string="Brands", domain="[['buyer_rank', '=', 1]]")


