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



class SalesXlsx(models.AbstractModel):
    _name = 'report.taps_sale.report_oa_zipper_xls'
    _inherit = 'report.report_xlsx.abstract'
    
    
    def generate_xlsx_report(self, workbook, data, orders):
        for order in orders:
           
            # One sheet by partner
            sheet = workbook.add_worksheet("Report")
            bold = workbook.add_format({'bold': True})
            sheet.write(0, 0, order.name, bold)