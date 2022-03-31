# -*- coding: utf-8 -*-
import base64
from odoo import models, fields, api



class ShiftSetup(models.Model):
    _name = 'shift.setup'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']    
    _description = 'Shift Setup'    

    code = fields.Char('Code', store=True, readonly=True, default='New', required=True)
    name = fields.Char(string="Shift Name", index=True)
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)
    inTime = fields.Float(string="In-Time")
    outTime = fields.Float(string="Out-Time")
    graceinTime = fields.Float(string="Grace In-Time")
    lunchinTime = fields.Float(string="Lunch In-Time")
    lunchoutTime = fields.Float(string="Lunch Out-Time")
    generalOT = fields.Float(string="General OT End Time")
    excessOT = fields.Float(string="Excess OT End Time")
    
    def name_get(self):
        result = []
        for record in self:
            name = record.code  + ' - ' +  record.name
            result.append((record.id, name))
        return result
    
    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
    
    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            vals['code'] = self.env['ir.sequence'].next_by_code('shift.setup.code')
        return super(ShiftSetup, self).create(vals)
