import json
import datetime
import math
import operator as py_operator
import re
from datetime import datetime, date, timedelta, time
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from itertools import groupby

from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare, float_round, float_is_zero, format_datetime
from odoo.tools.misc import format_date

from odoo.addons.stock.models.stock_move import PROCUREMENT_PRIORITIES

from werkzeug.urls import url_encode
from datetime import datetime



class PackingReport(models.Model):
    _name = "packing.report"
    _description = "Packing Production Report"
    _check_company_auto = True

    date_from = fields.Date('Date from', required=True, default = (date.today().replace(day=1)).strftime('%Y-%m-%d'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-%d'))


    @api.model
    def retrieve_dashboard(self):
        """ This function returns the values to populate the custom dashboard in
            the purchase order views.
        """
        raise UserError((self.date_from))
        self.check_access_rights('read')
        povalue = 0

        result = {
            'regular': 0,#all_to_send
            'block': 0,#all_waiting
            'replacement': 0,#all_late
            
            'samplepi': 0,
            'sa': 0,
            'pi': 0,
            'oa': 0,
            'budget_value': 0,#all_avg_order_value
            'expense_value': 0,#all_avg_days_to_purchase
            'expense_percent': 0,#all_total_last_7_days
            'due_amount': 0,#all_sent_rfqs
            
        }

        # currency = self.env.company.currency_id
        # result['company'] = self.env.company.id
        # current_datetime = datetime.now()


        # first_date_of_current_month = current_datetime.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        # last_date_of_current_month = first_date_of_current_month + relativedelta(day=31)
        # # raise UserError((first_date_of_current_month))
        # so = self.env['sale.order']
        # result['regular'] = so.search_count([('state', '=', 'sale'),('pi_type','=','regular')])
        
        # result['replacement'] = so.search_count([('state', '=', 'sale'),('pi_type','=','replacement')])
        # result['samplepi'] = so.search_count([('state', '=', 'sale'),('pi_type','=','samplepi')])
        # result['sa'] = so.search_count([('state', '=', 'sale'),('sales_type','=','sample'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        # result['pi'] = so.search_count([('state', '=', 'sale'),('sales_type','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        # result['oa'] = so.search_count([('state', '=', 'sale'),('sales_type','=','oa'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])

        # so = self.env['sale.order'].search([('sales_type','=','sale'),('state','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        # result['pi_total'] = "{:.2f}".format(sum(so.mapped('total_product_qty')))
        # result['pi_total_value'] ="{:.3f}".format(sum(so.mapped('amount_total'))/1000000)

        # so = self.env['sale.order'].search([('sales_type','=','oa'),('state','=','sale'),('date_order','>=',first_date_of_current_month),('date_order','<=',last_date_of_current_month)])
        # result['oa_total'] = "{:.2f}".format(sum(so.mapped('total_product_qty')))
        # result['oa_total_value'] ="{:.3f}".format(sum(so.mapped('amount_total'))/1000000)
        # raise UserError((result['company']))

        # result['regular'] = self.date_from
        return result



    
    




