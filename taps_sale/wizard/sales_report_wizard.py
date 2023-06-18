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
_logger = logging.getLogger(__name__)

class SalesReport(models.TransientModel):
    _name = 'sale.pdf.report'
    _description = 'All Sales Report'    

    
    date_from = fields.Date('Date from', required=True, default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_type = fields.Selection([
        ('pi',	'PI'),
        ('oa',	'OA'),
        ('sa',	'SA'),],
        string='Report Type', required=False,
        help='By Salary Head Wise Report')
    
    holiday_type = fields.Selection([
        ('company', 'By Company')],
        string='Report Mode', required=True, default='employee',
        help='By Employee: Allocation/Request for individual Employee, By Employee Tag: Allocation/Request for group of employees in category')
    
    
    bank_id = fields.Many2one(
        'res.bank',  string='Bank', readonly=False, ondelete="restrict", required=False)
    
 
    
    
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    
    
    
    
    company_all = fields.Selection([
        ('allcompany', 'TEX ZIPPERS (BD) LIMITED'),
        ('zipper','ZIPPER' ),
        ('metal','METAL TRIMS')],
        string='All Company', required=False)   
    
    file_data = fields.Binary(readonly=True, attachment=False)

