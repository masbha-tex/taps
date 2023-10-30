# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import math
from odoo.exceptions import UserError
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

class Contract(models.Model):
    _inherit = 'hr.contract'

    def _assign_open_contract(self):
        for contract in self:
            contract.employee_id.sudo().write({'contract_id': contract.id})
            contract.date_end = None

    def write(self, vals):
        res = super(Contract, self).write(vals)
        if vals.get('date_start'):
            for employee in self.employee_id.resume_line_ids.filtered(lambda c: not c.date_end):
                employee.name = employee.company_id.street
                employee.date_start = vals.get('date_start') or self.date_start
        if vals.get('date_end'):
            for employee in self.employee_id.resume_line_ids.filtered(lambda c: not c.date_end):
                employee.date_end = vals.get('date_end') or self.date_end
        if vals.get('date_end') is False:
            for employee in self.employee_id.resume_line_ids[0]:
                employee.date_end = None              
        return res

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    _order = "line_type_id, date_end desc, date_start desc"

    service_length = fields.Char( string="Service Length", compute='_calculate_serviceLength', store=True, readonly=True, depends=['date_start', 'date_end'])
    t_service_length = fields.Char(string="Total Service Length", compute='_t_calculate_serviceLength', readonly=True)
    year = fields.Integer( string="Year")
    month = fields.Integer( string="Month")

    def _calculate_serviceLength_schedule(self):
        line = self.env['hr.resume.line'].sudo().search([])
        emp_obj = self.env['hr.employee'].search([('active', '=', True)])
        for emp in emp_obj:
            if emp.resume_line_ids:
                first_resume = emp.resume_line_ids[0]
                if first_resume.employee_id.id == emp.id:
                    if emp.contract_id.date_start:
                        first_resume.date_start = emp.contract_id.date_start
            
        
        for record in line:
            if record:
                if record.date_end:
                    currentDate = datetime.strptime(str(record.date_end), '%Y-%m-%d')
                else:
                    currentDate = datetime.now() + timedelta(hours=6)
                    
                if record.date_start:
                    deadlineDate = datetime.strptime(str(record.date_start), '%Y-%m-%d')
                else:
                    deadlineDate = datetime.now() + timedelta(hours=6)
                if currentDate > deadlineDate:
                    currentDate, deadlineDate = deadlineDate, currentDate 
    
                # Calculate the difference in years and months using relativedelta
                delta = relativedelta(deadlineDate, (currentDate))

                years = delta.years
                total_months = delta.years * 12 + delta.months
                months = total_months % 12 

                # raise UserError((years,months))
    
                length = f"{years} Years {months} Months"
                record.year = years
                record.month = months               
                record.service_length = length
            else:
                record.service_length = f" "      

    def _calculate_serviceLength(self):
        # emp_obj = self.env['hr.employee'].search([('active', '=', True)])
        for record in self:
            if record:
                if record.date_end:
                    currentDate = datetime.strptime(str(record.date_end), '%Y-%m-%d')
                else:
                    currentDate = datetime.now() + timedelta(hours=6)
                    
                if record.date_start:
                    deadlineDate = datetime.strptime(str(record.date_start), '%Y-%m-%d')
                else:
                    deadlineDate = datetime.now() + timedelta(hours=6)
                if currentDate > deadlineDate:
                    currentDate, deadlineDate = deadlineDate, currentDate 
    
                # Calculate the difference in years and months using relativedelta
                delta = relativedelta(deadlineDate, (currentDate))

                years = delta.years
                total_months = delta.years * 12 + delta.months
                months = total_months % 12 

                # raise UserError((years,months))
    
                length = f"{years} Years {months} Months"
                record.year = years
                record.month = months               
                record.service_length = length
            else:
                record.service_length = f" "                 
                
    def _t_calculate_serviceLength(self):
        years = sum(dt['year'] for dt in self)
        months = sum(dt['month'] for dt in self)
        for record in self:
            if record:                
                m_fraction = math.floor(months/12)
                actual_month = 0
                if m_fraction < 1 :
                    actual_month = months
                else:
                    years += m_fraction
                    actual_month = (months - (m_fraction*12))
                    
                length = f"{years} Years {actual_month} Months"
                # raise UserError((length))
                record.t_service_length = length
            else:
                record.t_service_length = False
                