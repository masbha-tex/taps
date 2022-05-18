import base64
import io
import logging
from odoo import models, fields, api
from datetime import datetime, date, timedelta, time
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import xlsxwriter
from odoo.tools import format_date
from datetime import timedelta
import re
import math

class Attreprocess(models.TransientModel):
    _name = 'att.reprocess'
    _description = 'Attendance Reprocess'      

    date_from = fields.Date('Date from', required=True, 
                            default = (date.today().replace(day=1) - timedelta(days=1)).strftime('%Y-%m-26'))
    date_to = fields.Date('Date to', required=True, default = fields.Date.today().strftime('%Y-%m-25'))
    report_by = fields.Selection([
        ('employee', 'By Employee'),
        ('company', 'By Company'),
        ('department', 'By Department'),
        ('category', 'By Employee Tag'),
        ('emptype', 'By Employee Type')],
        string='Report Mode', required=True, default='employee')
    
    employee_id = fields.Many2one(
        'hr.employee',  string='Employee', index=True, readonly=False, ondelete="restrict")    
    
    category_id = fields.Many2one(
        'hr.employee.category',  string='Employee Tag', help='Category of Employee', readonly=False)
    mode_company_id = fields.Many2one(
        'res.company',  string='Company Mode', readonly=False)
    department_id = fields.Many2one(
        'hr.department',  string='Department', readonly=False)
    is_download = fields.Boolean(readonly=False, default=False)
    
    
    file_data = fields.Binary(readonly=True, attachment=False)    
    
    @api.depends('employee_id', 'report_by')
    def _compute_department_id(self):
        for holiday in self:
            if holiday.employee_id:
                holiday.department_id = holiday.employee_id.department_id
            elif holiday.report_by == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
            else:
                holiday.department_id = False
                
    #@api.depends('report_by')
    def _compute_from_report_by(self):
        for holiday in self:
            if holiday.report_by == 'employee':
                if not holiday.employee_id:
                    holiday.employee_id = self.env.user.employee_id
                holiday.mode_company_id = False
                holiday.category_id = False
                holiday.department_id = False
            elif holiday.report_by == 'company':
                if not holiday.mode_company_id:
                    holiday.mode_company_id = self.env.company.id
                holiday.category_id = False
                holiday.department_id = False
                holiday.employee_id = False
            elif holiday.report_by == 'department':
                if not holiday.department_id:
                    holiday.department_id = self.env.user.employee_id.department_id
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.category_id = False
            elif holiday.report_by == 'category':
                if not holiday.category_id:
                    holiday.category_id = self.env.user.employee_id.category_ids
                holiday.employee_id = False
                holiday.mode_company_id = False
                holiday.department_id = False
            #else:
            #    holiday.employee_id = self.env.context.get('default_employee_id') or self.env.user.employee_id
                
    # generate PDF report
    def action_att_reprocess(self):
        if self.report_by == "employee":#employee  company department category
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': self.employee_id.id,
                    'is_download': self.is_download}

        if self.report_by == "company":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': self.mode_company_id.id, 
                    'department_id': False, 
                    'category_id': False, 
                    'employee_id': False,
                    'is_download': self.is_download}

        if self.report_by == "department":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': self.department_id.id, 
                    'category_id': False, 
                    'employee_id': False,
                    'is_download': self.is_download}

        if self.report_by == "category":
            data = {'date_from': self.date_from, 
                    'date_to': self.date_to, 
                    'mode_company_id': False, 
                    'department_id': False, 
                    'category_id': self.category_id.id, 
                    'employee_id': False,
                    'is_download': self.is_download}
#         raise UserError(('domain'))        
        #return self.env.ref('taps_hr.report_salary_sheet').report_action(self, data=data)
        domain = []
        zkdomain = []
        if data.get('date_from'):
            domain.append(('attDate', '>=', data.get('date_from')))
            zkdomain.append(('punching_time', '>=', data.get('date_from')))
        if data.get('date_to'):
            domain.append(('attDate', '<=', data.get('date_to')))
            zkdomain.append(('punching_time', '<=', data.get('date_to')))
        if data.get('mode_company_id'):
            domain.append(('employee_id.company_id.id', '=', data.get('mode_company_id')))
        if data.get('department_id'):
            domain.append(('employee_id.department_id.id', '=', data.get('department_id')))
        if data.get('category_id'):
            domain.append(('employee_id.category_ids.id', '=', data.get('category_id')))
        if data.get('employee_id'):
            domain.append(('employee_id.id', '=', data.get('employee_id')))
        
        
        
        
        emp_att = self.env['hr.attendance'].search(domain)#.sorted(key = 'employee_id', reverse=False)
        
        emplist = emp_att.mapped('employee_id.id')
        
        zkdomain.append(('employee_id.id', 'in', (emplist)))
        
        
        if self.is_download == True:
            zk_attendance = self.env['zk.machine.attendance'].search(zkdomain).sorted(key = 'barcode').sorted(key = 'punching_time')
            if zk_attendance:
                for zkatt in zk_attendance:
                    att_Date = datetime.strptime(zkatt.punching_time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                    fromdatetime = zkatt.punching_time
                    myfromtime = datetime.strptime('000000','%H%M%S').time()
                    fromdatetime = datetime.combine(fromdatetime, myfromtime)

                    todatetime = datetime.now() + timedelta(hours=6)
                    mytotime = datetime.strptime('235959','%H%M%S').time()
                    todatetime = datetime.combine(todatetime, mytotime)
                    
                    att_var = emp_att.search([('employee_id', '=', zkatt.employee_id.id),
                                              ('attDate','=', att_Date)])
                    shiftgroup = self.env['shift.transfer'].search([('name', '=',zkatt.employee_id.id),
                                                                    ('activationDate','<=', att_Date)])
                    shift_group = shiftgroup.sorted(key = 'activationDate', reverse=True)[:1]
                    dayHour = 24

                    officeInTime = shift_group.inTime
                    officeOutTime = shift_group.outTime

                    thresholdin = officeInTime - 5

                    verifySlotDateTime = fromdatetime + timedelta(hours=thresholdin)
                    slot_beign = verifySlotDateTime

                    if verifySlotDateTime > (zkatt.punching_time + timedelta(hours=6)):
                        slot_beign = verifySlotDateTime - timedelta(days=1)

                    slot_beign = slot_beign - timedelta(hours=6)
                    slot_end = slot_beign + timedelta(hours=dayHour)
                    get_zk_att = zk_attendance.search([('employee_id', '=', zkatt.employee_id.id),
                                                       ('punching_time', '>=', slot_beign), 
                                                       ('punching_time', '<=', slot_end)])
                    get_zk_sort_asc = get_zk_att.sorted(key = 'punching_time')[:1]
                    get_zk_sort_desc = get_zk_att.sorted(key = 'punching_time', reverse=True)[:1]
                    zk_ck_in = get_zk_sort_asc.punching_time
                    zk_ck_out = get_zk_sort_desc.punching_time

                    slot_beign = slot_beign + timedelta(hours=5)
                    slot_beign_date = datetime.strptime(slot_beign.strftime('%Y-%m-%d'), '%Y-%m-%d')
                    slot_end_date = datetime.strptime(slot_end.strftime('%Y-%m-%d'), '%Y-%m-%d')


                    if zk_ck_in:
                        zk_in_date = datetime.strptime(zk_ck_in.strftime('%Y-%m-%d'), '%Y-%m-%d')
                        if att_var:
                            att_out = emp_att.search([('employee_id', '=', zkatt.employee_id.id),
                                                      ('attDate','=', slot_beign_date)])
                            if att_out:
                                if slot_beign_date == zk_in_date:
                                    if zk_ck_in != zk_ck_out:
                                        att_out.write({'check_in': zk_ck_in,
                                               'check_out': zk_ck_out})
                                    else:
                                        att_out.write({'check_in': zk_ck_in})
                                else:
                                    if slot_beign_date == slot_end_date:
                                        att_out.write({'check_in': zk_ck_in,
                                                       'check_out': zk_ck_out})
                                    else:
                                        att_out.write({'check_out': zk_ck_in})
            
            
        
        if self.is_download == False:
            if emp_att:
                for record in emp_att:
                    if record.check_in == False:
                        record[-1].write({'check_in': '2032-01-01 02:02:30','check_out': '2032-01-01 02:02:44'})
                        record[-1].write({'check_in': '','check_out': ''})
                    else:
                        if record.check_out == False:
                            record[-1].write({'check_out': '2032-01-01 02:02:50'})
                            record[-1].write({'check_out': ''})
                        else:
                            record[-1].write({'check_out': record.check_out + timedelta(seconds=1)})
                            record[-1].write({'check_out': record.check_out - timedelta(seconds=1)})
        
