
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime


class BusinessExcellence(models.Model):
    _name = 'business.excellence'
    _description = 'Business Excellence'
    _parent_name = 'parent_project_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # code = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True)
    code = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default='New')

    business_line = fields.One2many('business.excellence.task', 'business_id', string='AllocatedLine', copy=True)
    parent_project_id = fields.Many2one('business.excellence',
                                       string="Parent Project",
                                       ondelete="cascade",
                                       help="A project will inherit the tags of its parent project")
    name = fields.Char(required=True, translate=True)
    children_project_ids = fields.One2many('business.excellence', 'parent_project_id', string="Sub Project Name")
    # sub_project = fields.Char(string='Project')
    active = fields.Boolean('Active', default=True)
    company_id = fields.Many2one('res.company', 'Company')
    department_id = fields.Many2one('hr.department', 'Department', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    development = fields.Selection(selection=[
        ('1', 'Inhouse'),
        ('2', 'Outsource'),
        ('3', 'Inhouse & Outsource')], string="Development", tracking=True)
    type = fields.Selection([
        ('newproduct', 'New Product'),
        ('existingproduct', 'Existing Product'),
        ('newprocess', 'New Process'),
        ('existingprocess', 'Existing Process'),
        ],string="Innovation Area", required=True, default="newproduct")
    currency_id = fields.Many2one('res.currency', string='Currency')
    project_cost= fields.Monetary(string='Project Cost', store=True, currency_field='currency_id')
    date = fields.Date(string = "Start Date")
    finish_date = fields.Date(string = "Finish Date")
    count = fields.Integer(string="Est Days", compute="_compute_count")
    criteria_id = fields.Many2one('business.excellence.criteria', string='Scope')
    title_ids = fields.Many2one('business.excellence.title', string='Title', domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
    area_impact = fields.Many2many('business.excellence.impact', string="Area Impact")
    review = fields.Text('Review', tracking=True)
    conclusion = fields.Text('Conclusion', tracking=True)
    remarks = fields.Text('Special Remark', tracking=True)
    capitalize = fields.Selection(selection=[
        ('1', 'Capex'),
        ('2', 'New Upgradation'),
        ('3', 'Not Required')], string="Capitalize", tracking=True, default="3")
    machine = fields.Selection(selection=[
        ('1', 'New'),
        ('2', 'Upgradation')], string="Machine Status", tracking=True, default="1")
    # priority = fields.Selection([
    #         ('1', 'No Star'),
    #         ('2', 'One Star'),
    #         ('3', 'Two Star'),
    #         ('4', 'Three Star'),
    #         ('5', 'Four Star'),
    #         ('6', 'Five Star')], 'Priority', tracking=True, default='1')

    @api.depends('date', 'finish_date')
    def _compute_count(self):
        for record in self:
            if record.date and record.finish_date:
                count = (record.finish_date - record.date).days
                record.count = count
            else:
                record.count = 0

            
    @api.model
    def create(self, vals):
        if vals.get('code', _('New')) == _('New'):
            date = vals.get('date')
            vals['code'] = self.env['ir.sequence'].next_by_code('business.excellence', sequence_date=date)
        return super(BusinessExcellence, self).create(vals)

    # def view_task(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'My Task',
    #         'view_mode': 'tree,kanban',
    #         'res_model': 'business.excellence.line',
    #         # 'domain': [('business_id', '=', self.id)],
    #         # 'context': "{'create': False}"
            
    #     }

    def view_task(self):
        self.ensure_one()
        return {
            'name': _('%s _Task') % self.name,
            'view_mode': 'tree,form',
            'res_model': 'business.excellence.task',
            'type': 'ir.actions.act_window',
            # 'target': 'current',
            # 'domain': [('employee_id', '=', self.employee_id.id), ('deadline', '=', self.date_close)],
            # 'context': {'default_employee_id': self.employee_id.id},
            'domain': [('business_id', '=', self.id)],
            'context': {'create': True, 'default_criteria_id': self.criteria_id.id, 'default_business_id': self.id}
        }



# class BusinessExcellenceLine(models.Model):

#     _name = 'business.excellence.line'
#     _description = 'Business Excellence Line'
  
#     business_id = fields.Many2one('business.excellence', string='Project', index=True, required=True, ondelete='cascade')
#     # name = fields.Char(string="Description")
#     name = fields.Char('Task', required=True, translate=True)
#     # criteria_id = fields.Many2one('business.excellence.criteria', required=True, string='Title')
#     title_ids = fields.Many2one('business.excellence.title', string='Scope', domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
#     # active = fields.Boolean(string="Active", default="True")
    
    
    


