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

    #barcode = fields.Char(string='Badge ID')
    check_in = fields.Datetime(string = 'Check In',default=False, required=False, store=True, copy=True)


class ZkMachine(models.Model):
    _name = 'zk.machine'
    _description='ZK Machine'

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
        
    @api.model
    def cron_clear(self):
        machines = self.env['zk.machine'].search([])
        for machine in machines :
            machine.clear_attendance()
    
    def clear_attendance(self):
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        for info in self:
            machine_ip = info.name
            zk_port = info.port_no
            timeout = 15
            try:
                zk = ZK(machine_ip, port=zk_port, timeout=timeout, password=0, force_udp=False, ommit_ping=True)
            except NameError:
                raise UserError(_("Please install it with 'pip3 install pyzk'."))
            conn = self.device_connect(zk)
            if conn:
                conn.enable_device()
                clear_data = zk.get_attendance()
                if clear_data:
                    conn.clear_attendance()
                    self._cr.execute("""delete from zk_machine_attendance""")
                    conn.disconnect()
                    raise UserError('Attendance Records Deleted.')
                else:
                    raise UserError(_('Unable to clear Attendance log. Are you sure attendance log is not empty.'))
            else:
                raise UserError(_('Unable to connect to Attendance Device. Please use Test Connection button to verify.'))
            #except:
                #raise ValidationError(
                    #'Unable to clear Attendance log. Are you sure attendance device is connected & record is not empty.')

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
                        #atten_time = fields.Datetime.to_string(atten_time)
                        #officeTime = format_datetime(self.env, atten_time, dt_format=False)
                        #officeTime = str((officeTime[-8:])[:-3])
                        
                        fromdatetime = atten_time#datetime.now() + timedelta(hours=6)
                        #fromdatetime = datetime.strptime(fromdatetime.strftime('%Y-%m-%d 00:00:00'), '%Y-%m-%d 00:00:00')
                        myfromtime = datetime.strptime('000000','%H%M%S').time()
                        fromdatetime = datetime.combine(fromdatetime, myfromtime)
                        
                        todatetime = datetime.now() + timedelta(hours=6)
                        #todatetime = datetime.strptime(todatetime.strftime('%Y-%m-%d 23:59:59'), '%Y-%m-%d 23:59:59')
                        mytotime = datetime.strptime('235959','%H%M%S').time()
                        todatetime = datetime.combine(todatetime, mytotime)
                        
                        #getDate = datetime.now() + timedelta(hours=6)
                        #getDate = datetime.strptime(getDate.strftime('%Y-%m-%d'), '%Y-%m-%d')
                        if user:
                            for uid in user:
                                if uid.user_id == each.user_id:
                                    get_user_id = self.env['hr.employee'].search([('barcode', '=', each.user_id)])
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
                                            shiftgroup = self.env['shift.transfer'].search([('name', '=',get_user_id.id),
                                                                                            ('activationDate','<=', att_Date)])
                                            shift_group = shiftgroup.sorted(key = 'activationDate', reverse=True)[:1]
                                            dayHour = 24
                                            
                                            officeInTime = shift_group.inTime
                                            officeOutTime = shift_group.outTime

                                            thresholdin = officeInTime - 5
                                            
                                            verifySlotDateTime = fromdatetime + timedelta(hours=thresholdin)
                                            slot_beign = verifySlotDateTime
                        
                                            if verifySlotDateTime > (atten_time + timedelta(hours=6)):
                                                slot_beign = verifySlotDateTime - timedelta(days=1)

                                            slot_beign = slot_beign - timedelta(hours=6)
                                            slot_end = slot_beign + timedelta(hours=dayHour)
                                            get_zk_att = zk_attendance.search([('employee_id', '=', get_user_id.id),
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
                                                    att_out = att_obj.search([('employee_id', '=', get_user_id.id),
                                                                              ('attDate','=', slot_beign_date)])
                                                    if att_var.is_lock == True:
                                                        continue
                                                    else:
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

                                    else:
                                        pass
                                else:
                                    pass
                    # zk.enableDevice()
                    #conn.clear_attendance()
                    conn.disconnect
                    return True
                else:
                    continue
                    #raise UserError(_('Unable to get the attendance log, please try again later.'))
            else:
                break
                #raise UserError(_('Unable to connect, please check the parameters and network connections.'))
