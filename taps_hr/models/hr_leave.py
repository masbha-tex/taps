# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

# Copyright (c) 2005-2006 Axelor SARL. (http://www.axelor.com)

import logging
import math

from collections import namedtuple

from datetime import datetime, date, timedelta, time
from dateutil.rrule import rrule, DAILY
from pytz import timezone, UTC

from odoo import api, fields, models, SUPERUSER_ID, tools
from odoo.addons.base.models.res_partner import _tz_get
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import float_compare
from odoo.tools.float_utils import float_round
from odoo.tools.translate import _
from odoo.osv import expression
from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

class HolidaysRequest(models.Model):
    _inherit = "hr.leave"
    _description = "Time Off"
    
    def create_yearly_leave_allocation(self):
        #, empid, joindate, state
        stdate = (datetime.today().replace(day=1) - relativedelta(days=1)).strftime('%Y-%m-26')
        endate = (datetime.today() + relativedelta(month=12)).strftime('%Y-%m-25')
        raise UserError((stdate,endate))
        if state == 'open':
            
            base_auto = self.env['base.automation'].search([('id', '=', 23)])
            allocation = self.env['hr.leave.allocation'].search([('employee_id', '=', empid)])
            current_employee = self.env.user.employee_id
            if allocation:
                a='a'
            else:
                if base_auto:
                    base_auto.write({'active': False})
                date_join = datetime.strptime(joindate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                cl = 10.0
                sl = 14.0
                cl_days = round((cl/12)*(13-date_join.month))
                sl_days = round((sl/12)*(13-date_join.month))
                cl_days_int = int(cl_days)
                sl_days_int = int(sl_days)
                #raise UserError((cl_days_int,sl_days_int))
                
                allocation.create({'private_name': 'CL',
                                   'holiday_status_id': 107,										
                                   'employee_id': empid,
                                   'allocation_type': 'regular',
                                   'holiday_type': 'employee',
                                   'number_of_days': cl_days_int,
                                   'date_from': date.today(),
                                   'interval_unit': 'weeks',
                                   'interval_number': 1,
                                   'number_per_interval': 1,
                                   'unit_per_interval': 'hours',
                                   'state': 'validate',
                                   'first_approver_id': current_employee.id})
                
                allocation.create({'private_name': 'SL',
                                   'holiday_status_id': 115,										
                                   'employee_id': empid,
                                   'allocation_type': 'regular',
                                   'holiday_type': 'employee',
                                   'number_of_days': sl_days_int,
                                   'date_from': date.today(),
                                   'interval_unit': 'weeks',
                                   'interval_number': 1,
                                   'number_per_interval': 1,
                                   'unit_per_interval': 'hours',
                                   'state': 'validate',
                                   'first_approver_id': current_employee.id})
                if base_auto:
                    base_auto.write({'active': True})    
    

    def update_attendance(self,state,date_to,date_from,holiday_type,employee_id
                          ,mode_company_id,department_id,category_id):
        if state == 'validate':
            t_date = date_to.date()
            st_date = date_from.date()
            endd = (t_date - st_date).days
            att_obj = self.env['hr.attendance']
            if holiday_type == "employee":
                for d in range(0, endd+1):
                    get_att_data = att_obj.search([('employee_id', '=', employee_id.id),
                                                   ('attDate', '=', (st_date + timedelta(days=d)))])
                    get_att_data.generateAttFlag(get_att_data.empID,get_att_data.attDate,
                                                 get_att_data.inTime,get_att_data.check_in,
                                                 get_att_data.outTime,get_att_data.check_out) 

            if holiday_type == "company":
                for d in range(0, endd+1):
                    get_att_data = att_obj.search([('employee_id.company_id', '=', mode_company_id.id),
                                                   ('attDate', '=', (st_date + timedelta(days=d)))])
                    for comp in get_att_data:
                        get_att_data.generateAttFlag(comp.empID,comp.attDate,comp.inTime,comp.check_in,comp.outTime,comp.check_out)

            if holiday_type == "department":
                for d in range(0, endd+1):
                    get_att_data = att_obj.search([('employee_id.department_id', '=', department_id.id),
                                                   ('attDate', '=', (st_date + timedelta(days=d)))])
                    for dept in get_att_data:
                        get_att_data.generateAttFlag(dept.empID,dept.attDate,dept.inTime,dept.check_in, dept.outTime,dept.check_out)

            if holiday_type == "category":
                for d in range(0, endd+1):
                    get_att_data = att_obj.search([('employee_id.category_ids', '=', category_id.id),
                                                   ('attDate', '=', (st_date + timedelta(days=d)))])
                    for cat in get_att_data:
                        get_att_data.generateAttFlag(cat.empID,cat.attDate,cat.inTime,cat.check_in, cat.outTime,cat.check_out) 
        
        
        
        
        