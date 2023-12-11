
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, fields, api



class CustomerVisit(models.Model):

    _name = 'ccr.visit'
    _description = 'Customer Visit Template'


    name = fields.Char(string="Name")
    partner_id = fields.Many2one('res.partner', string='Customer')
    buyer = fields.Many2one('res.partner', string='Buyer')
    concern = fields.Char(string="Concern")
    designation = fields.Char(string="Designation")
    mobile = fields.Char(string="Mobile")
    product = fields.Char(string="Product")
    visit_purpose = fields.Char(string="Visit Purpose")
    visit_outcome = fields.Char(string="Visit Outcome")
    action = fields.Char(string="Action")
    # sales