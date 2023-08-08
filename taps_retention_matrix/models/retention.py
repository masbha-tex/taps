from odoo import models, fields, api, 

class RetentionMatrix(models.Model):
    _name = 'retention.retention'


    name = fields.Char(string="Name")