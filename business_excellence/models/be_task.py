from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta
from random import randint


class BusinessExcellenceTask(models.Model):
    _name = 'business.excellence.task'
    _description = 'Business Excellence Task'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "title_ids"
    _rec_name = 'title_ids'

    # name = fields.Char('Area Imapct', required=True)
    
    # company_id = fields.Many2one('res.company', string='Company')
    # title_ids = fields.One2many('business.excellence.title', 'criteria_id', string='Scope')
    # color = fields.Integer('Color Index')
    
    # def _get_default_color(self):
    #     return randint(1, 11)

    business_id = fields.Many2one('business.excellence', string='Project', index=True, required=True, ondelete='cascade')

    name = fields.Char('Name', required=False, translate=True)
    criteria_id = fields.Many2one('business.excellence.criteria', string='Scope')
    title_ids = fields.Many2one('business.excellence.title', required=True, string='Task', domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
    description = fields.Text('Description', tracking=True)
    start_date = fields.Date(string = "Start Date")
    finish_date = fields.Date(string = "Finish Date")
    attachment_no = fields.Text('Document No', tracking=True)
    attachment = fields.Binary('Evidence', attachment=True)
    state = fields.Selection([
            ('Active', 'Active'),
            ('Inprocess', 'Inprocess'),
            ('Hold', 'Hold'),
            ('Rejected', 'Rejected'),
            ('Not Started', 'Identified/Not Started'),
            ('Completed', 'Completed')], 'Status', required=True, tracking=True, default='Active')

    attachment_ids = fields.Many2many('ir.attachment', string='Attachments')
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments', tracking=True)

    def action_open_attachments(self):
        return {
            'name': 'Attachments',
            'view_type': 'tree',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'domain': [('id', 'in', self.attachment_ids.ids)],
            'target': 'current',
            }
        # res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        # res['domain'] = [('res_model', '=', 'business.excellence.task'), ('res_id', 'in', self.ids)]
        # res['context'] = {
        #     'default_res_model': 'business.excellence.task',
        #     'default_res_id': self.id,
        # }
        # return res    

    def action_get_attachment_view(self):
        res = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        res['domain'] = [('res_model', '=', 'business.excellence.task'), ('res_id', 'in', self.ids)]
        res['context'] = {
            'default_res_model': 'business.excellence.task',
            'default_res_id': self.id,
        }
        return res 

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'business.excellence.task'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for task in self:
            task.attachment_number = attachment.get(task.id, 0)  


        
    # active = fields.Boolean('Active', default=True)
    # color = fields.Integer('Color', default=_get_default_color)

    # @api.model
    # def create(self, vals):
    #     if vals.get('name', 'BE') == 'BE':
    #         vals['name'] = self.env['ir.sequence'].next_by_code('business.excellence.task.code')
    #     return super(RetentionMatrix, self).create(vals)

    _sql_constraints = [
        ('name_uniq', 'unique(title_ids)', 'The name of the Business Excellence Task must be unique!'),]      

    # @api.model
    # def create(self, vals):
    #     return super(Title, self).create(vals)

    # def write(self, vals):
    #     return super(Title, self).write(vals)      

