# -*- coding:utf-8 -*-
from odoo import models, fields, api

class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    emp_id = fields.Char(related = 'employee_id.emp_id', related_sudo=False, string="Emp ID", readonly=True, store=True)
    #category = fields.Many2many(related = 'employee_id.category_ids', related_sudo=False, string='Category', store=True)
    serviceLength = fields.Char(related = 'employee_id.serviceLength', related_sudo=False, string='Service Length', store=True)
    
    basic = fields.Monetary('Basic', readonly=True, store=True, tracking=True, help="Employee's monthly basic wage.")
    houseRent = fields.Monetary('House Rent', readonly=True, store=True, tracking=True, help="Employee's monthly HRA wage.")
    medical = fields.Monetary('Medical', readonly=True, store=True, tracking=True, help="Employee's monthly medical wage.")
    
    """e_ for Earnings head & d_ for Deduction head"""
    
    e_convence = fields.Boolean(string="Convence Allowance", store=True, tracking=True, help="Employee's monthly Convence Allowance.")
    e_food = fields.Boolean(string="Food Allowance", store=True, tracking=True, help="Employee's monthly Food Allowance.")
    e_tiffin = fields.Boolean(string="Tiffin Allowance", store=True, tracking=True, help="Employee's monthly Tiffin Allowance.")
    e_strenghtSnacks = fields.Boolean(string="Strenght Snacks Allowance", store=True, tracking=True, help="Employee's monthly Strenght Snacks Allowance.")
    e_attBonus = fields.Monetary(string="Att Bonus", store=True, tracking=True, help="Employee's monthly Attendance Bonus.")
    e_mobileInternet = fields.Monetary(string="Mobile & Internet Allowance", store=True, tracking=True, help="Employee's monthly Mobile & Internet Allowance.")
    e_car = fields.Monetary(string='Car Allowance', store=True, tracking=True, help="Employee's monthly Car Allowance.")
    e_others = fields.Monetary(string='Others Allowance', store=True, tracking=True, help="Employee's monthly Others Allowance.")
    e_incentive = fields.Monetary(string='Incentive Allowance', store=True, tracking=True, help="Employee's monthly Incentive Allowance.")
    
    d_ait = fields.Monetary(string='AIT Deduction', store=True, tracking=True, help="Employee's monthly AIT Deduction.")
    d_others = fields.Monetary(string='Others Deduction', store=True, tracking=True, help="Employee's monthly Others Deduction.")
    
    isActivePF = fields.Boolean(string="PF Active", store=True, tracking=True, help="Employee's monthly PF Contribution is Active.")
    pf_activationDate = fields.Date('PF Active Date', store=True, tracking=True, help="Activation Date of the PF Contribution.")
    
    @api.depends('employee_id')
    def _compute_employee_contract_ref(self):
        for contract in self.filtered('employee_id'):
            contract.name = contract.employee_id.emp_id
