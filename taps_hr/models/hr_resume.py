# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from datetime import date, datetime, time, timedelta
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models

class Employee(models.Model):
    _inherit = 'hr.employee'

    @api.model_create_multi
    def create(self, vals_list):
        res = super(Employee, self).create(vals_list)
        resume_lines_values = []
        for employee in res:
            line_type = self.env.ref('hr_skills.resume_type_experience', raise_if_not_found=False)
            resume_lines_values.append({
                'employee_id': employee.id,
                'name': employee.company_id.name or '',
                'date_start': employee.create_date.date(),
                'description': employee.job_title or '',
                'line_type_id': line_type and line_type.id,
            })
        self.env['hr.resume.line'].create(resume_lines_values)
        return res

class ResumeLine(models.Model):
    _inherit = 'hr.resume.line'
    _description = "Resumé line of an employee"
    # _order = "line_type_id, date_end desc, date_start desc"

    service_length = fields.Char( string="Service Length", compute='_calculate_serviceLength', store=True, readonly=True, depends=['date_start', 'date_end'])#
    t_service_length = fields.Char( string="Total Service Length", compute='_t_calculate_serviceLength', store=False, readonly=True)# 
    service_length_days = fields.Integer( string="Service Length Days", compute='_d_calculate_serviceLength', store=True, readonly=True, depends=['date_start', 'date_end'])
    total_service_length = fields.Char( string="Grand Total Service Length")
    year = fields.Integer( string="Year")
    month = fields.Integer( string="Month")

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

    
                # Calculate the remaining days
                # remaining_days = (deadlineDate - (currentDate + relativedelta(years=years, months=months))).days
    
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
                # Calculate years from total number of days
                # years = total_days // 365
                # remaining_days = total_days % 365
                
                # # Calculate months from the remaining days
                # months = remaining_days // 30
                # remaining_days %= 30
                m_fraction = math.floor(months/12)
                
                actual_month = 0
                if m_fraction < 1 :
                    actual_month = months
                elif m_fraction == 1 :
                    actual_month = 0
                    years += 1
                else:
                    years += m_fraction
                    actual_month = (months - (m_fraction*12))
                    
    
                length = f"{years} Years {actual_month} Months"
                
                record.t_service_length = length
                record.total_service_length = length
            else:
                record.t_service_length = False
                
    def _d_calculate_serviceLength(self):
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
    
                delta = deadlineDate - currentDate
                record.service_length_days = delta.days
            else:
                record.service_length_days = 0                

                
            #     record[-1].sudo().write({'service_length_days': delta.days})
            # else:
            #     record.sudo().write({'service_length_days': False})