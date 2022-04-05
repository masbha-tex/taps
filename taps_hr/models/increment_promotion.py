import base64

from datetime import date, datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, _
from odoo.addons.hr_payroll.models.browsable_object import BrowsableObject, InputLine, WorkedDays, Payslips, ResultRules
from odoo.exceptions import UserError, ValidationError
from odoo.tools import float_round, date_utils
from odoo.tools.misc import format_date
from odoo.tools.safe_eval import safe_eval


class IncrementPromotion(models.Model):
    _name = 'increment.promotion'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Increment Promotion'
    
    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, default='IP')
    increment_month = fields.Date('Increment Month', store=True, default=date.today().strftime('%Y-%m-01'))
    increment_line = fields.One2many('increment.promotion.line', 'increment_id', string='Increment Lines', store=True)
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'IP') == 'IP':
            vals['name'] = self.env['ir.sequence'].next_by_code('increment.code')
        return super(IncrementPromotion, self).create(vals)


class IncrementPromotionLine(models.Model):
    _name = 'increment.promotion.line'
    _description = 'Increment Promotion Line'
    
    increment_id = fields.Many2one('increment.promotion', string='Increment Reference', index=True, required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    job_id = fields.Char(related = 'employee_id.job_id.name', related_sudo=False, string='Position', readonly=True, store=True)
    new_job_id = fields.Many2one('hr.job', 'New Job Position', store=True)
    grade = fields.Char(related = 'employee_id.contract_id.structure_type_id.default_struct_id.name', related_sudo=False, string='Grade', readonly=True, store=True)
    new_grade = fields.Many2one('hr.payroll.structure.type', 'New Grade', store=True)
    ot_type = fields.Selection([('True', "Yes"),('False', "No")], string="OT Type", store=True)
    increment_percent = fields.Float(string='Increment Percent', store=True)
    increment_amount = fields.Float(string='Increment Amount', store=True)
    
    
#     @api.onchange('mode_type')
#     def onchange_partner_id(self):
#         self.increment_type = ''
#         for rec in self:
#             if rec.mode_type == 'False':
#                 return {'domain':{'increment_type': [('is_deduction','=',False)]}}
#             if rec.mode_type == 'True':
#                 return {'domain':{'increment_type': [('is_deduction','=',True)]}}
    
    
