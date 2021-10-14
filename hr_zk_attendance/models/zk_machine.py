# -*- coding: utf-8 -*-
import pytz
import sys
import datetime
import logging
import binascii

from . import zklib
from .zkconst import *
from struct import unpack
from odoo import api, fields, models
from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import format_datetime
from datetime import timedelta
_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError:
    _logger.error("Please Install pyzk library.")

_logger = logging.getLogger(__name__)


class HrAttendance(models.Model):
    _inherit = 'hr.attendance'

    barcode = fields.Char(string='Badge ID')


class ZkMachine(models.Model):
    _name = 'zk.machine'

    name = fields.Char(string='Machine IP', required=True)
    port_no = fields.Integer(string='Port No', required=True)
    address_id = fields.Many2one('res.partner', string='Working Address')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id.id)

    def device_connect(self, zk):
        try:
            conn = zk.connect()
            return conn
        except:
            return False

    def clear_attendance(self):
        for info in self:
            try:
                machine_ip = info.name
                zk_port = info.port_no
                timeout = 30
                try:
                    zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0, force_udp=False, ommit_ping=True)
                except NameError:
                    raise UserError(_("Please install it with 'pip3 install pyzk'."))
                conn = self.device_connect(zk)
                if conn:
                    conn.enable_device()
                    clear_data = zk.get_attendance()
                    if clear_data:
                        # conn.clear_attendance()
                        self._cr.execute("""delete from zk_machine_attendance""")
                        conn.disconnect()
                        raise UserError(_('Attendance Records Deleted.'))
                    else:
                        raise UserError(_('Unable to clear Attendance log. Are you sure attendance log is not empty.'))
                else:
                    raise UserError(
                        _('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            except:
                raise ValidationError(
                    'Unable to clear Attendance log. Are you sure attendance device is connected & record is not empty.')

    def getSizeUser(self, zk):
        """Checks a returned packet to see if it returned CMD_PREPARE_DATA,
        indicating that data packets are to be sent

        Returns the amount of bytes that are going to be sent"""
        command = unpack('HHHH', zk.data_recv[:8])[0]
        if command == CMD_PREPARE_DATA:
            size = unpack('I', zk.data_recv[8:12])[0]
            print("size", size)
            return size
        else:
            return False

    def zkgetuser(self, zk):
        """Start a connection with the time clock"""
        try:
            users = zk.get_users()
            print(users)
            return users
        except:
            return False

    @api.model
    def cron_download(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines :
            machine.download_attendance()

    def download_attendance(self):
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        zk_attendance = self.env['zk.machine.attendance']
        att_obj = self.env['hr.attendance']
        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            timeout = 15
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0, force_udp=False, ommit_ping=True)
            except NameError:
                raise UserError(_("Pyzk module not Found. Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                # conn.disable_device() #Device Cannot be used during this time.
                try:
                    user = conn.get_users()
                except:
                    user = False
                try:
                    attendance = conn.get_attendance()
                except:
                    attendance = False
                if attendance:
                    for each in attendance:
                        atten_time = each.timestamp
                        atten_time = datetime.strptime(atten_time.strftime('%Y-%m-%d %H:%M:%S'), '%Y-%m-%d %H:%M:%S')
                        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
                        local_dt = local_tz.localize(atten_time, is_dst=None)
                        utc_dt = local_dt.astimezone(pytz.utc)
                        utc_dt = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                        atten_time = datetime.strptime(utc_dt, "%Y-%m-%d %H:%M:%S")
                        att_Date = datetime.strptime(atten_time.strftime('%Y-%m-%d'), '%Y-%m-%d')
                        atten_time = fields.Datetime.to_string(atten_time)
                        #officeTime = format_datetime(self.env, atten_time, dt_format=False)
                        #officeTime = str((officeTime[-8:])[:-3])
                        
                        fromdatetime = datetime.now() + timedelta(hours=6)
                        #fromdatetime = datetime.strptime(fromdatetime.strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d 00:00:00')
                        myfromtime = datetime.strptime('000000','%H%M%S').time()
                        fromdatetime = datetime.combine(fromdatetime, myfromtime)
                        todatetime = datetime.now() + timedelta(hours=6)
                        #todatetime = datetime.strptime(todatetime.strftime('%Y-%m-%d 23:59:59'), '%Y-%m-%d 23:59:59')
                        mytotime = datetime.strptime('235959','%H%M%S').time()
                        todatetime = datetime.combine(todatetime, mytotime)
                        
                        getDate = datetime.now() + timedelta(hours=6)
                        getDate = datetime.strptime(getDate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                        if user:
                            for uid in user:
                                if uid.user_id == each.user_id:
                                    get_user_id = self.env['hr.employee'].search(
                                        [('barcode', '=', each.user_id)])
                                    if get_user_id:
                                        duplicate_atten_ids = zk_attendance.search(
                                            [('barcode', '=', each.user_id), ('punching_time', '=', atten_time)])
                                        if duplicate_atten_ids:
                                            continue
                                        else:
                                            zk_attendance.create({'employee_id': get_user_id.id,
                                                                  'barcode': each.user_id,
                                                                  'attendance_type': str(each.status),
                                                                  'punch_type': str(each.punch),
                                                                  'punching_time': atten_time,
                                                                  'address_id': info.address_id.id})
                                            
                                            att_var = att_obj.search([('employee_id', '=', get_user_id.id),
                                                                      ('attDate','=', att_Date)])
                                            get_zk_att = zk_attendance.search([('employee_id', '=', get_user_id.id),
                                                                               ('punching_time', '>=', fromdatetime), 
                                                                               ('punching_time', '<=', todatetime)])
                                            get_zk_sort_asc = get_zk_att.sorted(key = 'punching_time')[:1]
                                            get_zk_sort_desc = get_zk_att.sorted(key = 'punching_time', reverse=True)[:1]
                                            zk_ck_in = get_zk_sort_asc.punching_time
                                            zk_ck_out = get_zk_sort_desc.punching_time
                                            zk_inhour = format_datetime(self.env, zk_ck_in, dt_format=False)
                                            zk_inhour = str((zk_inhour[-8:])[:-3])
                                            zk_outhour = format_datetime(self.env, zk_ck_out, dt_format=False)
                                            zk_outhour = str((zk_outhour[-8:])[:-3])
                                            
                                            if att_var:
                                                att_in = att_var.search([('employee_id', '=', get_user_id.id),
                                                                         ('attDate','=', att_Date),
                                                                         ('check_in', '=', False),
                                                                         ('check_out', '=', False)])
                                                if att_in:
                                                    #raise UserError(_(zk_ck_in))
                                                    att_in.write({'check_in': zk_ck_in,
                                                                  'inHour': zk_inhour,
                                                                  'inFlag': 'P',
                                                                  'check_out': zk_ck_out,
                                                                  'outHour' : zk_outhour,
                                                                  'outFlag': 'TO'})
                                                    
                                                else:
                                                    att_out = att_in.search([('employee_id', '=', get_user_id.id),
                                                                             ('attDate','=', att_Date)])
                                                    att_out[-1].write({'check_out': zk_ck_out,
                                                                       'outHour' : zk_outhour,
                                                                       'outFlag': 'TO'})
                                            else:
                                                y = atten_time.strftime("%X")
                                                if y<myfromtime:
                                                    pre_date = att_Date - timedelta(days=1)
                                                    att_pre = att_obj.search([('employee_id', '=', get_user_id.id),
                                                                              ('attDate','=', pre_date)])
                                                    att_pre[-1].write({'check_out': atten_time})
                                                else:
                                                    get_tr = self.env['shift.transfer'].search([('name', '=',
                                                                                                 get_user_id.id),
                                                                                                ('activationDate',
                                                                                                 '<=', getDate)])
                                                    trans_data = get_tr.sorted(key = 'activationDate', reverse=True)[:1]
                                                    att_var.create({'attDate' : getDate,
                                                                    'employee_id': get_user_id.id,
                                                                    'check_in': zk_ck_in,
                                                                    'inHour': zk_inhour,
                                                                    'inFlag': 'P',
                                                                    'check_out': zk_ck_out,
                                                                    'outHour' : zk_outhour,
                                                                    'outFlag':'PO',
                                                                    'inTime': trans_data.inTime,
                                                                    'outTime': trans_data.outTime})
                                    else:
                                        pass
                                else:
                                    pass
                    # zk.enableDevice()
                    conn.disconnect
                    return True
                else:
                    raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
