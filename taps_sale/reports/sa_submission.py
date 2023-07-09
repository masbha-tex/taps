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


class SaSubmission(models.AbstractModel):
    _name = 'report.taps_sale.report_sa_submission_mt'
    _description = 'SA SUBMISSION FORM'      
    
    def _get_report_values(self, docids, data=None):
        
        # raise UserError((docids))     
        docs = self.env['sale.order.line'].search([('order_id', '=', docids)])
    
          
        return {
            'doc_ids': docs.ids,
            'doc_model': 'sale.order.line',
            'docs': docs,
            
        
        }