from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from random import randint


class Criteria(models.Model):
    _name = 'business.excellence.task'
    _description = 'Business Excellence Task'
    _inherit = ['mail.thread']
    _order = "name"
    _rec_name = 'name'

    # name = fields.Char('Area Imapct', required=True)
    
    # company_id = fields.Many2one('res.company', string='Company')
    # title_ids = fields.One2many('business.excellence.title', 'criteria_id', string='Scope')
    # color = fields.Integer('Color Index')
    
    # def _get_default_color(self):
    #     return randint(1, 11)

    business_id = fields.Many2one('business.excellence', string='Project', index=True, required=True, ondelete='cascade')

    name = fields.Char('Task', required=True, translate=True)
    title_ids = fields.Many2one('business.excellence.title', string='Scope', domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
    description = fields.Text('Description', tracking=True)
    start_date = fields.Date(string = "Start Date")
    finish_date = fields.Date(string = "Finish Date")
    attachment_no = fields.Text('Document No', tracking=True)
    attachment = fields.Text('Evidence', tracking=True)
    # active = fields.Boolean('Active', default=True)
    # color = fields.Integer('Color', default=_get_default_color)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'BE') == 'BE':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('business.excellence.task.code')
    #     return super(RetentionMatrix, self).create(vals)

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'The name of the Business Excellence Task must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

