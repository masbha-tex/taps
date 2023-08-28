import re
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError

class MachineList(models.Model):
    _name = "machine.list"
    _description = "Machine List"
    _check_company_auto = True

    name = fields.Char(string='Machine Name', store=True, required=True)
    capacity = fields.Integer(string='Capacity', store=True, default=0, required=True)
    max_lots = fields.Integer(string='Max Lots', store=True, default=0, required=True)

