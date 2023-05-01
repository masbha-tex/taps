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
    
    name = fields.Char('Code', store=True,required=True, readonly=True, index=True, copy=False, tracking=True, default='IP')
    increment_month = fields.Date('Increment Month', store=True, tracking=True, default=date.today().strftime('%Y-%m-01'))
    increment_line = fields.One2many('increment.promotion.line', 'increment_id', string='Increment Lines',tracking=True, store=True, required=True)
    state = fields.Selection([
    ('draft', 'To Submit'),
    ('submit', 'Submitted'),
    ('approved', 'Approved'),
    ('refused', 'Refused')], string='Status', copy=False, 
        index=True, readonly=True, store=True, default='draft', tracking=True, help="Status of the Increment")
    

    
    def button_approve(self, force=False):
        if self.increment_line:
            for app in self.increment_line:
                elist = self.env['hr.employee'].search([('id','=',app.employee_id.id)])
                conlist = self.env['hr.contract'].search([('employee_id','=',app.employee_id.id)])
                if app.new_job_id:
                    elist[-1].write({'job_id': app.new_job_id.id})
                    conlist[-1].write({'job_id': app.new_job_id.id})
                if app.new_grade:
                    conlist[-1].write({'structure_type_id': app.new_grade.id})
                if app.increment_amount > 0:
                    conlist[-1].write({'wage': app.employee_id.contract_id.wage + app.increment_amount})
                if app.ot_type == "true":
                    elist[-1].write({'isovertime': True})
                if app.ot_type == "false":
                    elist[-1].write({'isovertime': False})
                if not app.new_category == app.category:
                    conlist[-1].write({'category': app.new_category})
#                     if elist.company_id.id == 2:#HeadOffice
#                         if app.new_category == 'staff':
#                             elist[-1].write({'category_ids': 15})
#                         elif app.new_category == 'expatriate':
#                             elist[-1].write({'category_ids': 16})
#                     if elist.company_id.id == 1:#Zipper
#                         if app.new_category == 'staff':
#                             elist[-1].write({'category_ids': 31})
#                         elif app.new_category == 'worker':
#                             elist[-1].write({'category_ids': "Z-Worker"})
#                         elif app.new_category == 'expatriate':
#                             elist[-1].write({'category_ids': 32})
#                     if elist.company_id.id == 3:#MetalTrims
#                         if app.new_category == 'staff':
#                             elist[-1].write({'category_ids': 21})
#                         elif app.new_category == 'worker':
#                             elist[-1].write({'category_ids': 20})
#                         elif app.new_category == 'expatriate':
#                             elist[-1].write({'category_ids': 22})
#                     if elist.company_id.id == 4:#Contructual
#                         if app.new_category == 'staff':
#                             if elist.category_ids.name == 'C-Zipper Worker':
#                                 elist[-1].write({'category_ids': 47})
#                             elif elist.category_ids.name == 'C-Button Worker':
#                                 elist[-1].write({'category_ids': 44})
#                             elif elist.category_ids.name == 'C-Worker':
#                                 elist[-1].write({'category_ids': 26})
                            
#                         elif app.new_category == 'worker':
#                             if elist.category_ids.name == 'C-Zipper Staff':
#                                 elist[-1].write({'category_ids': 42})
#                             elif elist.category_ids.name == 'C-Button Staff':
#                                 elist[-1].write({'category_ids': 43})
#                             elif elist.category_ids.name == 'C-Staff':
#                                 elist[-1].write({'category_ids': 25})
                        
        self.write({'state': 'approved'})
        return {}

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'submit']:
                continue
            order.write({'state': 'submit'})
        return True     
    
    def button_draft(self):
        self.write({'state': 'draft'})
        return {}    
    
    def button_cancel(self):
        self.write({'state': 'refused'})        
    
    @api.model
    def create(self, vals):
        if vals.get('name', 'IP') == 'IP':
            vals['name'] = self.env['ir.sequence'].next_by_code('increment.code')
        return super(IncrementPromotion, self).create(vals)
    
    def write(self, vals):
        for line in self:
            if line.state in ['approved']:
                raise UserError(_('Cannot update a Increment Data which is in state \'%s\'.') % (line.state,))
        return super(IncrementPromotion, self).write(vals)     
    
    def unlink(self):
        for line in self:
            if line.state in ['submit', 'refused', 'approved']:
                raise UserError(_('Cannot delete a Increment Data which is in state \'%s\'.') % (line.state,))
        return super(IncrementPromotion, self).unlink()      
    


class IncrementPromotionLine(models.Model):
    _name = 'increment.promotion.line'
    _description = 'Increment Promotion Line'
    
    increment_id = fields.Many2one('increment.promotion', string='Increment Reference', index=True, required=True, ondelete='cascade')
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, store=True)
    job_id = fields.Many2one('hr.job', 'Position', store=True, readonly=True, compute='_compute_job_id')
    new_job_id = fields.Many2one('hr.job', 'New Job Position', store=True)
    grade = fields.Many2one('hr.payroll.structure.type', 'Grade', store=True, readonly=True, compute='_compute_job_id')
    new_grade = fields.Many2one('hr.payroll.structure.type', 'New Grade', store=True)
    old_ot_type = fields.Boolean("old OT Type", readonly=False, store=True, compute='_compute_job_id')
    ot_type = fields.Selection([('true', 'Yes'),('false', 'No')], compute='onchange_ot_type', string="OT Type", store=True, readonly=False)
    gross = fields.Char('Gross', store=True, readonly=True, compute='_compute_job_id')
    new_gross = fields.Float(string='New Gross',readonly=False, compute='_compute_salary_breakdown', store=True)
    basic = fields.Char('Basic', store=True, readonly=True, compute='_compute_job_id')
    new_basic = fields.Float(string='New Basic',readonly=False, compute='_compute_salary_breakdown', store=True)
    hra = fields.Char('HRA', store=True, readonly=True, compute='_compute_job_id')
    new_hra = fields.Float(string='New House Rent',readonly=False, compute='_compute_salary_breakdown', store=True)
    medical = fields.Char('Medical', store=True, readonly=True, compute='_compute_job_id')
    new_medical = fields.Float(string='New Medical',readonly=False, compute='_compute_salary_breakdown', store=True)
    category = fields.Selection([('staff', 'Staff'),('worker', 'Worker'),('expatriate', 'Expatriate')], 'Category', store=True, readonly=True, compute='_compute_job_id')
    new_category = fields.Selection([('staff', 'Staff'),('worker', 'Worker'),('expatriate', 'Expatriate')], 'New Category', compute='onchange_type', readonly=False, store=True)
    increment_percent = fields.Float(string='Increment Percent',readonly=False, compute='calculate_percents', store=True)
    increment_amount = fields.Float(string='Increment Amount',readonly=False, compute='calculate_percent', store=True)
    
    
    @api.depends('employee_id','category','increment_amount')
    def _compute_salary_breakdown(self):
        self.new_basic = '0.0'
        self.new_hra = '0.0'
        self.new_medical = '0.0'
        
        for inc in self:
            wage = inc.employee_id.contract_id.wage
            if inc.category == 'staff':
                inc.new_gross = wage+inc.increment_amount
                inc.new_basic = inc.new_gross*0.60
                inc.new_hra = (inc.new_gross*0.30)
                inc.new_medical = (inc.new_gross*0.10)
                #return {'domain':{'adjustment_type': [('is_deduction','=',False)]}}
            if inc.category == 'worker':
                inc.new_gross = wage+inc.increment_amount
                inc.new_basic = (inc.new_gross-1450)/1.5
                inc.new_hra = ((inc.new_gross-1450)/1.5)*0.50
                inc.new_medical = 1450.00
            if inc.category == 'expatriate':
                inc.new_gross = wage+inc.increment_amount
                inc.new_basic = inc.new_gross*0.60
                inc.new_hra = (inc.new_gross*0.30)
                inc.new_medical = (inc.new_gross*0.10)
    
    @api.depends('employee_id')
    def _compute_job_id(self):
        for line in self.filtered('employee_id'):
            line.job_id = line.employee_id.job_id.id
            line.grade = line.employee_id.contract_id.structure_type_id
            line.old_ot_type = line.employee_id.isovertime
            line.gross = line.employee_id.contract_id.wage
            line.basic = line.employee_id.contract_id.basic
            line.hra = line.employee_id.contract_id.houseRent
            line.medical = line.employee_id.contract_id.medical
            line.category = line.employee_id.contract_id.category
            
    
    @api.depends('employee_id')
    def onchange_ot_type(self):
        for ot in self:
            if ot.employee_id:
                ottype = ot.employee_id.isovertime
                if ottype:
                    #raise UserError(('sfefefe'))
                    ot.ot_type = 'true'
                else:
                    ot.ot_type = 'false'
            #return ot.ot_type
#             ot.department_id = ot.employee_id.department_id

    @api.depends('employee_id')
    def onchange_type(self):
        for type in self:
            if type.employee_id:
                type.new_category = type.category
    
    
    @api.onchange('employee_id','increment_percent')
    def calculate_amount(self):
        for inc in self:
            wage = inc.employee_id.contract_id.wage            
            if inc.category == 'worker':
                wage = inc.employee_id.contract_id.basic
            if inc.increment_percent:
                inc.increment_amount = (wage*inc.increment_percent)/100
            
    @api.onchange('employee_id','increment_amount')
    def calculate_percent(self):
        for inc in self:
            wage = inc.employee_id.contract_id.wage            
            if inc.category == 'worker':
                wage = inc.employee_id.contract_id.basic            
            if inc.increment_amount:
                inc.increment_percent = (100*inc.increment_amount)/wage     
                
    @api.depends('employee_id')
    def calculate_percents(self):
        for inc in self:
            wage = inc.employee_id.contract_id.wage            
            if inc.category == 'worker':
                wage = inc.employee_id.contract_id.basic
            if inc.increment_amount:
                inc.increment_percent = (100*inc.increment_amount)/wage  
            
    def unlink(self):
        for line in self:
            if line.increment_id.state in ['submit', 'refused', 'approved']:
                raise UserError(_('Cannot delete a Increment line which is in state \'%s\'.') % (line.increment_id.state,))
        return super(IncrementPromotionLine, self).unlink()

    def write(self, vals):
        for line in self:
            if line.increment_id.state in ['approved']:
                raise UserError(_('Cannot update a Increment line which is in state \'%s\'.') % (line.increment_id.state,))
        return super(IncrementPromotionLine, self).write(vals)    