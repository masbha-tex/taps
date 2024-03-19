
from odoo import models, fields, api, _ 
from odoo.exceptions import ValidationError, UserError
from datetime import date, datetime



class HrHealthSafety(models.Model):
    _name = 'hr.health.safety'
    _description = 'Health & Safety'
    _inherit = ['mail.thread', 'mail.activity.mixin']    

    name = fields.Char(string="Number", required=True, index=True, copy=False, readonly=True, default=_('New')) 
    active = fields.Boolean('Active', default=True)
    employee_id = fields.Many2one('hr.employee', "Employee", tracking=True, required=True)    
    company_id = fields.Many2one(related='employee_id.company_id', store=True)
    department_id = fields.Many2one(related='employee_id.department_id', store=True)
    joining_date = fields.Date(related = 'employee_id.joining_date', related_sudo=False, string='Joining Date', store=True)
    service_length = fields.Char(related = 'employee_id.service_length', related_sudo=False, string='Service Length', store=True)
    accident_date = fields.Date(string = "Date of Accident Occurred")
    shift = fields.Selection(selection=[
        ('1', 'Day'),
        ('2', 'Night'),
        ('3', 'Common')], string="Shift", tracking=True, help="How likely is it that this employee will shift?" )   
    type = fields.Selection(selection=[
        ('1', 'Critical Severity'),
        ('2', 'High Severity'),
        ('3', 'Low Severity'),
        ('4', 'Major Severity')], string="Severity", tracking=True)
    accident_nature = fields.Selection(selection=[
        ('1', 'Negligience of Work'),
        ('2', 'Negligence at work (SOP not maintained)'),
        ('3', 'Machine Related'),
        ('4', 'Lack of Awareness'),
        ('5', 'PPE Related'),
        ('6', 'Safety related'),
        ('7', 'Slips trips & fall related'),
        ('8', 'Operation related'),
        ('9', 'Movement related'),
        ('10', 'Ergonomic'),
        ('11', 'Instrument related'),
        ('12', 'Hot work related'),
        ('13', 'Environment related'),
        ('14', 'Chemical related')], string="Nature  of Accident", tracking=True)
    treatment_type = fields.Selection(selection=[
        ('1', 'Lost Time'),
        ('2', 'Medical Case'),
        ('3', 'First Aid / BEPZA Medical'),
        ('4', 'No Treatment'),
        ('5', 'Lost Days')], string="Treatment Type", tracking=True)
    accident_type = fields.Selection(selection=[
        ('Injury', 'Injury'),
        ('Illness', 'Illness'),
        ('Psychological', 'Psychological'),
        ('Harassment', 'Harassment'),
        ('Others', 'Others')], string="Type of Accident", tracking=True)
    description_accident = fields.Text('Description of Accident', tracking=True)
    corrective_action = fields.Text('Corrective Action', tracking=True)
    preventive_action = fields.Text('Preventive Action', tracking=True)
    remarks = fields.Text('Remarks', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    treatment_expense = fields.Monetary(string='Treatment Expense', store=True, currency_field='currency_id')
    rejoining_date = fields.Date(string = "Date of Re-Joining")
    count = fields.Integer(string="Leave Days", compute="_compute_count")
    last_day_acc = fields.Integer(string="Days since last accident", compute="_compute_last_day_acc")
    
    
    # criteria_id = fields.Many2one('hs.criteria', required=True, string='')
    # title_ids = fields.Many2one('hs.title', string='Title', required=True, domain="['|', ('criteria_id', '=', False), ('criteria_id', '=', criteria_id)]")
    @api.depends('rejoining_date', 'accident_date')
    def _compute_count(self):
        for record in self:
            if record.rejoining_date and record.accident_date:
                count = (record.rejoining_date - record.accident_date).days
                record.count = count
            else:
                record.count = 0 
                
    @api.depends('accident_date')
    def _compute_last_day_acc(self):
        acc_ = self.env['hr.health.safety'].search([], order='accident_date desc', limit=1)
        if acc_:
            acc_date = acc_.accident_date
            today = date.today()
            count = (today - acc_date).days
            self.last_day_acc = count
        else:
            self.last_day_acc = 0
        # for record in self:
        #     if record.accident_date:
        #         count = (record.date.today() - record.accident_date).days
        #         record.count = count
        #     else:
        #         record.count = 0 

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            accident_date = vals.get('accident_date')
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.health.safety', sequence_date=accident_date)
        return super(HrHealthSafety, self).create(vals)
