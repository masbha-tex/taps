# -*- coding:utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError,ValidationError
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from datetime import date, datetime, time, timedelta
from dateutil.rrule import rrule, DAILY, WEEKLY
from odoo.addons.resource.models.resource_mixin import timezone_datetime
from odoo.addons.resource.models.resource import datetime_to_string, string_to_datetime, Intervals
from odoo.tools.float_utils import float_round
from odoo.tools import date_utils, float_utils
import math
import pytz


class HrContract(models.Model):
    _inherit = 'hr.contract'
    
    emp_id = fields.Char(related = 'employee_id.emp_id', related_sudo=False, string="Emp ID", readonly=True, store=True)
    service_length = fields.Char(related = 'employee_id.service_length', related_sudo=False, string='Service Length', store=True)
    
    basic = fields.Monetary('Basic', readonly=True, store=True, tracking=True,compute='_compute_salary_breakdown',
                            help="Employee's monthly basic wage.")
    houseRent = fields.Monetary('House Rent', readonly=True, store=True, tracking=True,
                                compute='_compute_salary_breakdown',help="Employee's monthly House Rent wage.")
    medical = fields.Monetary('Medical', readonly=True, store=True, tracking=True, 
                              compute='_compute_salary_breakdown',help="Employee's monthly medical wage.")
    
    category = fields.Selection([('staff', 'Staff'),('worker', 'Worker'),('expatriate', 'Expatriate')], string='Emp Type', tracking=True, help='Employee Type of the contract', store=True, required=True)
    
    """e_ for Earnings head & d_ for Deduction head"""
    e_convence = fields.Boolean(string="Convence Allowance", store=True, tracking=True, 
                                help="Employee's monthly Convence Allowance.")
    e_food = fields.Boolean(string="Food Allowance", store=True, tracking=True, help="Employee's monthly Food Allowance.")
    e_tiffin = fields.Boolean(string="Tiffin Allowance", store=True, tracking=True, help="Employee's monthly Tiffin Allowance.")
    e_strenghtSnacks = fields.Boolean(string="Strenght Snacks Allowance", store=True, tracking=True, 
                                      help="Employee's monthly Strenght Snacks Allowance.")
    e_attBonus = fields.Monetary(string="Att Bonus", store=True, tracking=True, help="Employee's monthly Attendance Bonus.")
    e_car = fields.Monetary(string='Car Allowance', store=True, tracking=True, help="Employee's monthly Car Allowance.")
    e_others = fields.Monetary(string='Others Allowance', store=True, tracking=True, help="Employee's monthly Others Allowance.")
   
    d_ait = fields.Monetary(string='AIT Deduction', store=True, tracking=True, help="Employee's monthly AIT Deduction.")
    d_others = fields.Monetary(string='Others Deduction', store=True, tracking=True, help="Employee's monthly Others Deduction.")
   
    isActivePF = fields.Boolean(string="PF Active", store=True, tracking=True, 
                                help="Employee's monthly PF Contribution is Active.")
    pf_activationDate = fields.Date('PF Active Date', store=True, tracking=True, help="Activation Date of the PF Contribution.")

    def create_att_atjoin(self, empid, joindate, leavdate, state):
        if state == 'open':
            base_auto = self.env['base.automation'].search([('id', '=', 23)])
            attendance = self.env['hr.attendance'].search([('employee_id', '=', empid)])
            if attendance:
                a='a'
            else:
                if base_auto:
                    base_auto.write({'active': False})
                date_join = datetime.strptime(joindate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                stdate = date_join.replace(day=26)
                c_date = datetime.now()
                end_date = c_date.strptime(c_date.strftime('%Y-%m-%d'), '%Y-%m-%d')
                #st_date = t_date.replace(day=26) - relativedelta(months = 1)
                if joindate.day<26:
                    stdate = stdate - relativedelta(months = 1)

                #raise UserError((end_date,stdate))
                delta = end_date - stdate
                for i in range(delta.days + 1):
                    day = stdate + timedelta(days=i)
                    if date_join > day:
                        attendance.create({'attDate': day,
                                           'employee_id': empid,
                                           'inTime': False,
                                           'outTime': False,
                                           'inFlag':'X',
                                           'outFlag':'X',
                                           'inHour' : False,
                                           'outHour' : False})
                    else:
                        attendance.create({'attDate': day,
                                           'employee_id': empid,
                                           'inTime': False,
                                           'outTime': False,
                                           'inFlag':'A',
                                           'outFlag':'A',
                                           'inHour' : False,
                                           'outHour' : False})

                if base_auto:
                    base_auto.write({'active': True})
        
        #date_start
    
    def float_to_time(self,hours):
        if hours == 24.0:
            return time.max
        fractional, integral = math.modf(hours)
        return time(int(integral), int(float_round(60 * fractional, precision_digits=0)), 0)      
    
    @api.depends('employee_id')
    def _compute_employee_contract_ref(self):
        for contract in self.filtered('employee_id'):
            contract.name = contract.employee_id.emp_id
            
    @api.depends('category','wage')
    def _compute_salary_breakdown(self):
        self.basic = '0.0'
        self.houseRent = '0.0'
        self.medical = '0.0'
        for contract in self:
            if contract.category == 'staff':
                contract.basic = contract.wage*0.60
                contract.houseRent = (contract.wage*0.30)
                contract.medical = (contract.wage*0.10)
                #return {'domain':{'adjustment_type': [('is_deduction','=',False)]}}
            if contract.category == 'worker':
                contract.basic = (contract.wage-1450)/1.5
                contract.houseRent = ((contract.wage-1450)/1.5)*0.50
                contract.medical = 1450.00
            if contract.category == 'expatriate':
                contract.basic = contract.wage*0.60
                contract.houseRent = (contract.wage*0.30)
                contract.medical = (contract.wage*0.10)           
    
    def _get_default_work_entry_type(self):
        return self.env.ref('hr_work_entry.work_entry_type_attendance', raise_if_not_found=False)  
    
    def _get_leave_work_entry_type_dates(self, leave, date_from, date_to):
        return self._get_leave_work_entry_type(leave)

    def _get_leave_work_entry_type(self, leave):
        return leave.work_entry_type_id
    
    def _get_interval_leave_work_entry_type(self, interval, leaves):
        #raise UserError(('sdfefe'))
        for leave in leaves:
            if interval[0] >= leave[0] and interval[1] <= leave[1] and leave[2]:
                interval_start = interval[0].astimezone(pytz.utc).replace(tzinfo=None)
                interval_stop = interval[1].astimezone(pytz.utc).replace(tzinfo=None)
                return self._get_leave_work_entry_type_dates(leave[2], interval_start, interval_stop)
        return self.env.ref('hr_work_entry_contract.work_entry_type_leave')    
    
    def _get_contract_work_entries_values(self, date_start, date_stop):
        self.ensure_one()
        contract_vals = []
        employee = self.employee_id
        calendar = self.resource_calendar_id
        resource = employee.resource_id
        tz = pytz.timezone(calendar.tz)
        start_dt = pytz.utc.localize(date_start) if not date_start.tzinfo else date_start
        end_dt = pytz.utc.localize(date_stop) if not date_stop.tzinfo else date_stop
        #raise UserError((start_dt,end_dt))

        attendances = self.attendance_intervals_batch(employee.id,
            start_dt, end_dt, resources=resource, tz=tz
        )[resource.id]
        
        """domainatt =([('employee_id', '=', employee.id),
                     ('attDate', '>=', start_dt),
                     ('attDate','<=', end_dt)])
        attendances = self.env['hr.attendance'].search(domainatt)"""

        # Other calendars: In case the employee has declared time off in another calendar
        # Example: Take a time off, then a credit time.
        # YTI TODO: This mimics the behavior of _leave_intervals_batch, while waiting to be cleaned
        # in master.
        resources_list = [self.env['resource.resource'], resource]
        resource_ids = [False, resource.id]
        leave_domain = [
            ('time_type', '=', 'leave'),
            # ('calendar_id', '=', self.id), --> Get all the time offs
            ('resource_id', 'in', resource_ids),
            ('date_from', '<=', datetime_to_string(end_dt)),
            ('date_to', '>=', datetime_to_string(start_dt)),
            ('company_id', 'in', [False, self.company_id.id]),
        ]
        result = defaultdict(lambda: [])
        tz_dates = {}
        combine = datetime.combine
        for leave in self.env['resource.calendar.leaves'].search(leave_domain):
            addval = True
            for interval in attendances:
                if interval[2].attDate == leave.date_from.date():
                    addval = False
                    break
            if addval:
                for resource in resources_list:
                    if leave.resource_id.id not in [False, resource.id]:
                        continue
                    tz = tz if tz else pytz.timezone((resource or self).tz)
                    if (tz, start_dt) in tz_dates:
                        start = tz_dates[(tz, start_dt)]
                    else:
                        start = start_dt.astimezone(tz)
                        tz_dates[(tz, start_dt)] = start
                    if (tz, end_dt) in tz_dates:
                        end = tz_dates[(tz, end_dt)]
                    else:
                        end = end_dt.astimezone(tz)
                        tz_dates[(tz, end_dt)] = end
                    dt0 = string_to_datetime(leave.date_from).astimezone(tz)
                    dt1 = string_to_datetime(leave.date_to).astimezone(tz)
                    
                    hour_from = 9.0
                    hour_to = 18.0
                    
                    dt0 = tz.localize(combine(dt0.date(), self.float_to_time(hour_from)))
                    dt1 = tz.localize(combine(dt1.date(), self.float_to_time(hour_to)))
                
                    #dt0 = tz.localize(combine(attendance.attDate, self.float_to_time(hour_from)))
                
                    result[resource.id].append((max(start, dt0), min(end, dt1), leave))
        
        
        mapped_leaves = {r.id: Intervals(result[r.id]) for r in resources_list}
        
        leaves = mapped_leaves[resource.id]
        
        #raise UserError((mapped_leaves))
        real_attendances = attendances - leaves
        real_leaves = attendances - real_attendances#leaves#
        
        # A leave period can be linked to several resource.calendar.leave
        split_leaves = []
        for leave_interval in leaves:
            if leave_interval[2] and len(leave_interval[2]) > 1:
                split_leaves += [(leave_interval[0], leave_interval[1], l) for l in leave_interval[2]]
            else:
                split_leaves += [(leave_interval[0], leave_interval[1], leave_interval[2])]
        real_leaves = split_leaves
        #raise UserError((real_leaves))
        # Attendances 199168
        att_contract_vals = []        
        for interval in real_attendances:
            default_work_entry_type = self._get_default_work_entry_type()
            if interval[2].inFlag in ('F','A','X'):
                work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', interval[2].inFlag)])
                default_work_entry_type = work_entry_type#self._get_friday_work_entry_type()
            if interval[2].otHours>=2:
                work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'T')])
                default_work_entry_type = work_entry_type#self._get_friday_work_entry_type()
            if interval[2].inFlag in ('L'):
                work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'L')])
                default_work_entry_type = work_entry_type#self._get_friday_work_entry_type()
            if interval[2].outFlag in ('EO'):
                work_entry_type = self.env['hr.work.entry.type'].search([('code', '=', 'EO')])
                default_work_entry_type = work_entry_type#self._get_friday_work_entry_type()
                
            work_entry_type_id = default_work_entry_type
            # All benefits generated here are using datetimes converted from the employee's timezone
            contract_vals += [{
                #'name': "%s: %s" % (work_entry_type_id.name, employee.name),
                'name': interval[2].inFlag,
                'date_start': interval[0].astimezone(pytz.utc).replace(tzinfo=None),
                'date_stop': interval[1].astimezone(pytz.utc).replace(tzinfo=None),
                'work_entry_type_id': work_entry_type_id.id,
                'employee_id': employee.id,
                'contract_id': self.id,
                'company_id': self.company_id.id,
                'state': 'draft',
                'inFlag': interval[2].inFlag,
                'outFlag': interval[2].outFlag,
                'otHours': interval[2].otHours,
            }]
            
        for interval in real_leaves:
            #raise UserError(('sdfefefefefefef'))
            # Could happen when a leave is configured on the interface on a day for which the
            # employee is not supposed to work, i.e. no attendance_ids on the calendar.
            # In that case, do try to generate an empty work entry, as this would raise a
            # sql constraint error
            if interval[0] == interval[1]:  # if start == stop
                continue
            #if (real_attendances)
            leave_entry_type = self._get_interval_leave_work_entry_type(interval, real_leaves)
            interval_start = interval[0].astimezone(pytz.utc).replace(tzinfo=None)
            interval_stop = interval[1].astimezone(pytz.utc).replace(tzinfo=None)
            
            addval = True
            for interval in real_attendances:
                if interval[2].attDate == interval_start.date():
                    addval = False
                    break
            if addval:
                contract_vals += [dict([
                    #('name', "%s%s" % (leave_entry_type.name + ": " if leave_entry_type else "", employee.name)),
                    ('name', leave_entry_type.code),
                    ('date_start', interval_start),
                    ('date_stop', interval_stop),
                    ('work_entry_type_id', leave_entry_type.id),
                    ('employee_id', employee.id),
                    ('company_id', self.company_id.id),
                    ('state', 'draft'),
                    ('contract_id', self.id),
                ] + self._get_more_vals_leave_interval(interval, real_leaves))]
        return contract_vals
    
    def _get_work_entries_values(self, date_start, date_stop):
        """
        Generate a work_entries list between date_start and date_stop for one contract.
        :return: list of dictionnary.
        """
        vals_list = []
        for contract in self:
            contract_vals = contract._get_contract_work_entries_values(date_start, date_stop)

            # If we generate work_entries which exceeds date_start or date_stop, we change boundaries on contract
            if contract_vals:
                #raise UserError(('sdfdsf'))
                #Handle empty work entries for certain contracts, could happen on an attendance based contract
                #NOTE: this does not handle date_stop or date_start not being present in vals
                dates_stop = [x['date_stop'] for x in contract_vals if x['contract_id'] == contract.id]
                if dates_stop:
                    date_stop_max = max(dates_stop)
                    if date_stop_max > contract.date_generated_to:
                        contract.date_generated_to = date_stop_max

                dates_start = [x['date_start'] for x in contract_vals if x['contract_id'] == contract.id]
                if dates_start:
                    date_start_min = min(dates_start)
                    if date_start_min < contract.date_generated_from:
                        contract.date_generated_from = date_start_min

            vals_list += contract_vals

        return vals_list
    

    def attendance_intervals_batch(self, employee_id, start_dt, end_dt, resources=None, domain=None, tz=None):
        """ Return the attendance intervals in the given datetime range.
            The returned intervals are expressed in specified tz or in the resource's timezone.
        """
        #raise UserError((start,until))
        self.ensure_one()
        resources = self.env['resource.resource'] if not resources else resources
        assert start_dt.tzinfo and end_dt.tzinfo
        self.ensure_one()
        combine = datetime.combine

        resources_list = list(resources) + [self.env['resource.resource']]
        resource_ids = [r.id for r in resources_list]
        #domain = domain if domain is not None else []
        
        """domain = expression.AND([domain, [
            ('calendar_id', '=', self.id),
            ('resource_id', 'in', resource_ids),
            ('display_type', '=', False),
        ]])"""

        # for each attendance spec, generate the intervals in the date range
        cache_dates = defaultdict(dict)
        cache_deltas = defaultdict(dict)
        result = defaultdict(list)
        
        domainatt =([('employee_id', '=', employee_id), 
                                     ('attDate', '>=', start_dt),
                                     ('attDate','<=', end_dt)])
        
        attrecord = self.env['hr.attendance'].search(domainatt)
        attData = attrecord.sorted(key = 'attDate', reverse=False)
        for attendance in attData:
            for resource in resources_list:
                # express all dates and times in specified tz or in the resource's timezone
                tz = tz if tz else timezone((resource or self).tz)
                if (tz, start_dt) in cache_dates:
                    start = cache_dates[(tz, start_dt)]
                else:
                    start = start_dt.astimezone(tz)
                    cache_dates[(tz, start_dt)] = start
                if (tz, end_dt) in cache_dates:
                    end = cache_dates[(tz, end_dt)]
                else:
                    end = end_dt.astimezone(tz)
                    cache_dates[(tz, end_dt)] = end

                start = start.date()
                #if attendance.attDate:
                #    start = max(start, attendance.attDate)
                until = end.date()
                #if attendance.attDate:
                #    until = min(until, attendance.attDate)
                    
                #start = start + relativedelta(weeks=-1)
                #raise UserError((start,until))
                #attendance.attendance.weekday()
                #weekdays = attendance.check_in
                #weekday = int(weekdays.strftime("%w"))
                
                #days = rrule(WEEKLY, start, interval=2, until=until, byweekday=weekday)
                #days = rrule(DAILY, start, until=until, byweekday=weekday)
                #if i>0:
                
                k=0
                #for day in days:
                    #k +=1
                    # attendance hours are interpreted in the resource's timezone
                #raise UserError((cache_deltas))#
                
                hour_from = 0
                hour_to = 0
                if attendance.inFlag not in ('H','CL','SL','EL','ML','LW','OD','AJ'):
                    hour_from = 9.0
                    hour_to = 18.0
                if (tz, attendance.attDate, hour_from) in cache_deltas:
                    dt0 = cache_deltas[(tz, attendance.attDate, hour_from)]
                else:
                    dt0 = tz.localize(combine(attendance.attDate, self.float_to_time(hour_from)))
                    cache_deltas[(tz, attendance.attDate, hour_from)] = dt0
                
                    
                
                if (tz, attendance.attDate, hour_to) in cache_deltas:
                    dt1 = cache_deltas[(tz, attendance.attDate, hour_to)]
                else:
                    dt1 = tz.localize(combine(attendance.attDate, self.float_to_time(hour_to)))
                    cache_deltas[(tz, attendance.attDate, hour_to)] = dt1
                    #raise UserError((start_dt,end_dt,(max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance)))
                    #if k==5:
                    #    raise UserError((attendance.attDate))
                    #   raise UserError((day,(max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance)))
                result[resource.id].append((max(cache_dates[(tz, start_dt)], dt0), min(cache_dates[(tz, end_dt)], dt1), attendance))
        return {r.id: Intervals(result[r.id]) for r in resources_list}
