import logging
from odoo import api, fields, tools, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerAllocation(models.Model):
    _name = 'customer.allocation'
    _description = 'Salesperson Wise Customer'
    _inherit = ['format.address.mixin', 'image.mixin','portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    # _order = "name ASC, id DESC"
    # _rec_name="name"

    salesperson = fields.Many2one('res.partner', domain=[('share', '=', False),('sale_team_id', '!=', False)], string="Salesperson")
    team_id = fields.Many2one('crm.team', string= "Team", related="salesperson.sale_team_id")
    customers = fields.Many2many('res.partner', string="Customers")
    