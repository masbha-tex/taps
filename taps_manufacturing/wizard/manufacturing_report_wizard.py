import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
import re
import math



class ManufacturingPDFReport(models.TransientModel):
    _name = 'manufacturing.pdf.report'
    _description = 'Manufacturing Report'     

    
    date_from = fields.Date('Date from', required=True, default=(date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('job_card',	'Employee Job Card'),
        ('dailyatten',	'Daily Attendance'),        
        ('dailyatten_ot',	'Daily Attendance OT'),
        ('dailyatten_ots',	'Daily Attendance with OT'),
        ('daily_manpower',	'Daily Manpower Summary'),
        ('head_count',	'Head Count Report'),
        ('payroll_planning', 'Payroll Planning Report'),
        ('monthly_manhours', 'Monthly Manhours Report'),
        ('daily_manhours',	'Daily Manhours Report'),
        ('daily_ot_analysis',	'Daily OT Analysis'),
        ('daily_atten_summary',	'Daily Attendance Summary'), 
        ('monthly_atten_summary',	'Monthly Attendance Summary'),
        ('holiday_slip',	'Off Day/Holiday Duty Slip'),
        ('daily_excess_ot',	'Daily Excess OT'),
        ('daily_salary_cost',	'Daily Salary Cost'),
        ('atten_calender',	'Attendance Calender'),
        ('shift_schedule',       'Shift Schedule')],
        string='Report Type', required=True, default='job_card',
        help='By Attendance Reporting')
    atten_type = fields.Selection([
        ('p',	'Present'),
        ('l',	'Late'),
        ('a',	'Absent'),
        ('fp',	'Friday Present'),
        ('hp',	'Holiday Present'),
        ('eo',	'Early Out'),
        ('po',	'Pending Out'),
        ('cl',	'Casual Time Off'),
        ('sl',	'Seek Time Off'),
        ('el', 'Earn Time off'),
        ('ml', 'Metarnity Time off'),
        ('lw',	'Leave without pay'),
        ('co',	'C-Off'),
        ('aj',	'Adjustment Days'),],
        string='Attendance Type', required=False, #default='p',
        help='By Attendance Reporting')
    types = fields.Selection([
        ('morning', 'Morning Shift'),
        ('evening', 'Evening Shift'),
        ('night', 'Night Shift')
    ], string='Shift Type', index=True, store=True, copy=True)    
    
    mode_type = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Attendance Reporting for individual Employee, By Employee Tag: Attendance Reporting for group of employees in category')
    
