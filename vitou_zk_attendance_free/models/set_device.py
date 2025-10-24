# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

import datetime
import logging
from collections import defaultdict
from .lic.globals import func_mod

import pytz
import json

import numpy as np

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, time

from odoo.tools import date_utils, DEFAULT_SERVER_DATETIME_FORMAT

from odoo.tools import date_utils, DEFAULT_SERVER_DATETIME_FORMAT
from operator import attrgetter

import sys
import os
sys.path.insert(1,os.path.abspath("./pyzk"))

_logger = logging.getLogger(__name__)
try:
    from zk import ZK, const
except ImportError as e:
    _logger.error("Please Install pyzk library.", e)
    print(e)


class BiometricDeviceDetails(models.Model):
    """Model for configuring and connect the biometric device with odoo"""
    _name = 'vitouzkf.set.device'
    _description = 'Biometric Device Details'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', required=True, help='Record Name', tracking=True)
    device_ip = fields.Char(string='Device IP', required=True,
                            help='The IP address of the Device', tracking=True)
    port_number = fields.Integer(string='Port Number 1', required=True, help="The Port Number of the Device", tracking=True)
    port_number2 = fields.Integer(string='Port Number 2', required=True,
                                  help="The Port Number of the Device")
    port_number3 = fields.Integer(string='Port Number 3', required=True,
                                  help="The Port Number of the Device")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda
                                     self: self.env.user.company_id.id,
                                 help='Current Company')
    date_from = fields.Date(string="Date From", default=fields.Date.today)
    date_to = fields.Date(string="Date To", default=fields.Date.today)


    state = fields.Selection(
        string="State",
        selection=[
            ('posted', 'Posted'),
            ('done', 'Done'),
        ], default="posted", required=True, tracking=True
    )

    device_in_out = fields.Selection(
        string="Device In_Out",
        selection=[
            ('in', 'In'),
            ('out', 'Out'),
            ('both', 'Both'),
        ], default="both", required=True, tracking=True
    )

    #done
    done_uid = fields.Integer(string="Done UID")
    done_uname = fields.Char(string='Done UName')
    done_staff = fields.Char(string='Done Staff')
    done_date = fields.Char(string="Done Date")

    undodone_uid = fields.Integer(string="Undo Done UID")
    undodone_uname = fields.Char(string='Undo Done UName')
    undodone_staff = fields.Char(string='Undo Done Staff')
    undodone_date = fields.Char(string="Undo Done Date")

    done_uid = fields.Char(string="Done UID")
    done_date = fields.Char(string="Done Date")
    
    #cancel
    canceled_uid = fields.Char(string="Canceled UID")
    canceled_date = fields.Char(string="Canceled Date")

    def action_done(self):
        for rec in self:
            if rec.state == 'posted':
                rec.state = 'done'
                rec.done_uid = self.get_uid()
                rec.done_uname = self.get_uname()
                rec.done_staff = self.get_staff()
                rec.done_date = self.get_date()
            else:
                raise UserWarning('Invalid State!')

    def action_undodone(self):
        for rec in self:
            if rec.state == 'done':
                rec.state = 'posted'
                rec.undodone_uid = self.get_uid()
                rec.undodone_uname = self.get_uname()
                rec.undodone_staff = self.get_staff()
                rec.undodone_date = self.get_date()
            else:
                raise UserWarning('Invalid State!')


    def get_uid(self):
        return self.env.user.id

    def get_uname(self):
        return self.env.user.login

    def get_date(self):
        return fields.Datetime.now()

    def get_staff(self):
        return self.env[func_mod].get_staff(self.get_uid())


    def device_connect(self, zk):
        """Function for connecting the device with Odoo"""
        try:
            conn = zk.connect()
            return conn
        except Exception:
            return False

    @api.model
    def cron_download_attendance(self):
        """cron_download method: Perform a cron job to download attendance data for all machines.

          This method iterates through all the machines in the 'zk.machine' model and
          triggers the download_attendance method for each machine."""
        _logger.info("++++++++++++Cron Executed++++++++++++++++++++++")
        machines = self.env['vitouzkf.set.device'].search([])
        for machine in machines:
            machine.action_download_attendance()

    def action_test_connection(self):
        """Checking the connection status"""
        success_ports = []
        error_ports = []
        for rec in self:
            if rec.port_number:
                device_ip = rec.device_ip
                port = rec.port_number
                # print('device=',device_ip, ', port=', port )
                zk_1 = ZK(device_ip, port=port , timeout=30,
                      password=False, ommit_ping=False)
            try:
                if zk_1.connect():
                    success_ports.append(self.port_number)

                else:
                    error_ports.append(self.port_number)
            except Exception as e:
                error_ports.append(self.port_number)

        if self.port_number2:
            zk_2 = ZK(self.device_ip, port=self.port_number2, timeout=30,
                      password=False, ommit_ping=False)
            try:
                if zk_2.connect():
                    success_ports.append(self.port_number2)
                else:
                    error_ports.append(self.port_number2)
            except Exception as e:
                error_ports.append(self.port_number2)
        
        if self.port_number3:
            zk_3 = ZK(self.device_ip, port=self.port_number3, timeout=30,
                      password=False, ommit_ping=False)
            try:
                if zk_3.connect():
                    success_ports.append(self.port_number3)
                else:
                    error_ports.append(self.port_number3)
            except Exception as e:
                error_ports.append(self.port_number3)

        message = ""
        if success_ports:
            message += f'Successfully connected to ports: {success_ports}. '
        if error_ports:
            message += f'Failed to connect to ports: {error_ports}.'

        if success_ports:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': 'success',
                    'sticky': False
                }
            }
        else:
            raise ValidationError(message)

    def action_download_attendance(self):
        """Function to download attendance records from the device"""
        if (self.lic_check()):
            zk_attendance = self.env['vitouzkf.attendance.all']
            hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port_1 = info.port_number
            zk_port_2 = info.port_number2
            zk_port_5 = info.port_number3
            try:
                # Connecting with the device with the ip and port provided
                zk_1 = ZK(machine_ip, port=zk_port_1, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)
                zk_2 = ZK(machine_ip, port=zk_port_2, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)
                zk_3 = ZK(machine_ip, port=zk_port_5, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn_1 = self.device_connect(zk_1)
            conn_2 = self.device_connect(zk_2)
            conn_5 = self.device_connect(zk_3)
            if conn_1:
                conn_1.disable_device()
                conn_2.disable_device()
                conn_5.disable_device()
                attendance_1 = conn_1.get_attendance()
                attendance_2 = conn_2.get_attendance()
                attendance_5 = conn_5.get_attendance()
                if attendance_1 :
                    attendance_dict = defaultdict(list)
                    for attendance in [attendance_1]:
                        if attendance:
                            for each in attendance:
                                atten_time = each.timestamp
                                local_tz = pytz.timezone(
                                    self.env.user.partner_id.tz or 'GMT')
                                local_dt = local_tz.localize(atten_time, is_dst=None)
                                utc_dt = local_dt.astimezone(pytz.utc)
                                attendance_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                                atten_time_datetime = datetime.strptime(attendance_time, "%Y-%m-%d %H:%M:%S")
                                atten_date = atten_time_datetime.date()
                                if info.date_to <= atten_date <= info.date_from:
                                    attendance_dict[each.user_id].append(atten_time_datetime)
                    for user_id, atten_times in attendance_dict.items():
                        dates = {}
                        for atten_time in atten_times:
                            atten_date = atten_time.date()
                            if atten_date not in dates:
                                dates[atten_date] = []
                            dates[atten_date].append(atten_time)

                        for atten_date, times in dates.items():
                            times.sort()
                            if len(times) > 2:
                                times = [times[0], times[-1]]
                                dates[atten_date] = times
                            if len(times) == 1 and atten_date != datetime.now().date():
                                employee = self.env['hr.employee'].search([('device_id_num', '=', user_id)])
                                if employee:
                                    if employee.shift_id:
                                        shift_out = employee.shift_id.shift_out
                                        if shift_out:
                                            shift_out_time = times(int(shift_out-5), int(((shift_out + 5) % 1) * 60))
                                            checkout_datetime = datetime.combine(atten_date, shift_out_time)
                                            times.append(checkout_datetime)
                                            times.sort()
                                            dates[atten_date] = times

                        updated_atten_times = [time for times in dates.values() for time in times]
                        updated_atten_times.sort()
                        attendance_dict[user_id] = updated_atten_times

                        employee = self.env['hr.employee'].search([('device_id_num', '=', user_id)])
                        if len(employee) == 1:
                            for atten_time in updated_atten_times:
                                existing_attendance = zk_attendance.search(
                                    [('device_id_num', '=', user_id), ('check_out','=', False)], limit=1)
                                existing_hr_attendance = hr_attendance.search(
                                    [('employee_id', '=', employee.id),('check_out','=', False)], limit=1)
                                if existing_attendance:
                                    for exist in existing_attendance:
                                        if not exist.check_in == atten_time:
                                            if exist.check_in.date() == atten_time.date():
                                                if exist.check_in > atten_time:
                                                    exist.write({
                                                        'check_in': atten_time,
                                                        'check_out': exist.check_in,
                                                        'o_check': 'o',
                                                    })
                                                else:
                                                    if exist.check_out:
                                                        if not exist.check_out > atten_time:
                                                            exist.write({
                                                                'check_out': atten_time,
                                                                'o_check': 'o',
                                                            })
                                                            if existing_hr_attendance:
                                                                existing_hr_attendance.write({
                                                                    'employee_id': employee.id,
                                                                    'check_out':atten_time
                                                                })
                                                    else:
                                                        exist.write({
                                                            'check_out': atten_time,
                                                            'o_check': 'o',
                                                        })
                                                        if existing_hr_attendance:
                                                            existing_hr_attendance.write({
                                                                'employee_id': employee.id,
                                                                'check_out': atten_time
                                                            })
                                            else:
                                                if not exist.check_in == atten_time:
                                                    check_in_atten = zk_attendance.search([('check_in','=',atten_time), ('device_id_num','=',user_id)])
                                                    check_out_atten = zk_attendance.search([('check_out','=',atten_time), ('device_id_num','=',user_id)])
                                                    if not check_in_atten and not check_out_atten:
                                                        zk_attendance.create({
                                                            'employee_id': employee.id,
                                                            'check_in': atten_time,
                                                            'check_out': False,
                                                            'i_check': 'i',
                                                            'device_id_num': user_id
                                                        })
                                                        hr_attendance.create({
                                                            'employee_id':employee.id,
                                                            'check_in': atten_time
                                                        })
                                else:
                                    check_in_atten = zk_attendance.search(
                                        [('check_in', '=', atten_time), ('device_id_num', '=', user_id)])
                                    check_out_atten = zk_attendance.search(
                                        [('check_out', '=', atten_time), ('device_id_num', '=', user_id)])
                                    if not check_in_atten and not check_out_atten:
                                        zk_attendance.create({
                                            'employee_id': employee.id,
                                            'check_in': atten_time,
                                            'check_out': False,
                                            'device_id_num': user_id,
                                            'i_check': 'i',
                                        })
                                        hr_attendance.create({
                                            'employee_id': employee.id,
                                            'check_in': atten_time
                                        })

                        elif len(employee) > 1:
                            raise ValidationError(
                                "More Than One Employee Is Found With The Same Device Id" + user_id)

                conn_1.disconnect()
                conn_2.disconnect()
                conn_5.disconnect()
                return True
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
        else:
            raise UserError(_('Unable to get the attendance log, please'
                              'try again later.'))

    def action_restart_device(self):
        """For restarting the device"""
        try:

            zk_1 = ZK(self.device_ip, port=self.port_number, timeout=30,
                      password=0,
                      force_udp=False, ommit_ping=False)
            zk_2 = ZK(self.device_ip, port=self.port_number2, timeout=30,
                      password=0,
                      force_udp=False, ommit_ping=False)
            zk_5 = ZK(self.device_ip, port=self.port_number3, timeout=30,
                      password=0,
                      force_udp=False, ommit_ping=False)
            self.device_connect(zk_1).restart()
            self.device_connect(zk_2).restart()
            self.device_connect(zk_5).restart()
        except Exception as error:
            raise ValidationError(f'{error}')

    def action_download_attendance_all(self):
        """Function to download attendance records from the device"""
        if (self.lic_check()):
            zk_attendance = self.env['vitouzkf.attendance.all']
            hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port_1 = info.port_number

            try:
                # Connecting with the device with the ip and port provided
                zk_1 = ZK(machine_ip, port=zk_port_1, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)

            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn_1 = self.device_connect(zk_1)

            if conn_1:
                conn_1.disable_device()

                attendance_1 = conn_1.get_attendance()

                user = conn_1.get_users()
                print(user)
                print(attendance_1)
                if attendance_1:
                    attendance_dict = defaultdict(list)
                    for attendance in [attendance_1]:
                        if attendance:
                            print(attendance)
                            for each in attendance:
                                print(each.user_id, each.timestamp)

                                atten_time = each.timestamp
                                local_tz = pytz.timezone(
                                    self.env.user.partner_id.tz or 'GMT')
                                local_dt = local_tz.localize(atten_time, is_dst=None)
                                utc_dt = local_dt.astimezone(pytz.utc)
                                attendance_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")

                                attendance_time = self.convertDate_to_utc(atten_time)
                                atten_time_datetime = datetime.strptime(attendance_time, "%Y-%m-%d %H:%M:%S")
                                atten_date = atten_time_datetime.date()

                                print(atten_date)
                                if info.date_from <= atten_date <= info.date_to:
                                    attendance_dict[each.user_id].append(atten_time_datetime)
                                    print(each.user_id,'=',atten_date)
                                    user_id = each.user_id
                                    employee = self.env['hr.employee'].search([('device_id_num', '=', user_id)])
                                    print(employee)
                                    zkuser = self.env['vitouzkf.zk.user'].search([('user_id', '=', user_id)], limit=1)
                                    print(zkuser)
                                    print(each.user_id, '=',employee.device_id_num, '=', atten_time_datetime)
                                    if len(employee):
                                        print(employee)
                                        atten_time_post = self.convertDate_to_utc(atten_time)
                                        if len(employee) == 1:
                                            checkintype = employee.checkintype
                                            hour_resting = employee.hour_resting
                                            day = datetime.strftime(atten_time, "%d")
                                            check_in_atten = zk_attendance.search(
                                                [('check_in', '=', atten_time_post),
                                                 ('device_id_num', '=', user_id)])
                                            check_in_atten1 = zk_attendance.search(
                                                [('check_in', '=', atten_time_post),
                                                 ('device_id_num', '=', user_id)])
                                            #print(atten_time,'=', atten_time_post,'=',check_in_atten )
                                            print(check_in_atten,'=', len(check_in_atten), '=', len(check_in_atten1))
                                            if len(check_in_atten) == 0 :
                                                zk_attendance.create({
                                                    'employee_id': employee.id,
                                                    'zkuser': zkuser.name,
                                                    'check_in': atten_time_post,
                                                    'day': day,
                                                    'in_out': '',
                                                    'device_id_num': user_id,
                                                    'devicename': info.name,
                                                    'device_ip': info.device_ip,
                                                    'checkintype': checkintype,
                                                    'hour_resting': hour_resting,

                                                })


                                            else:
                                                if check_in_atten.state =='posted':
                                                    zk_attendance.write({
                                                        'employee_id': employee.id,
                                                        'zkuser': zkuser.name,
                                                        'check_in': atten_time_post,
                                                        'day': day,
                                                        'in_out': '',
                                                        'device_id_num': user_id,
                                                        'devicename': info.name,
                                                        'device_ip': info.device_ip,
                                                        'checkintype': checkintype,
                                                        'hour_resting': hour_resting,
                                                    })

                            return self.myinfo("Successful download attendance", "success")

                conn_1.disconnect()
                raise UserError(_('Successful down load attendance'))
                return True
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
        else:
            raise UserError(_('Unable to get the attendance log, please'
                              'try again later.'))

    def action_download_attendance_all(self):
        """Function to download attendance records from the device"""
    
        zk_attendance = self.env['vitouzkf.attendance.all']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port_1 = info.port_number
    
            try:
                # Connecting with the device with the ip and port provided
                zk_1 = ZK(machine_ip, port=zk_port_1, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)
    
            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn_1 = self.device_connect(zk_1)
    
            if conn_1:
                conn_1.disable_device()
    
                attendance_1 = conn_1.get_attendance()
    
                user = conn_1.get_users()
                print(user)
    
                if attendance_1:
                    attendance_dict = defaultdict(list)
                    for attendance in [attendance_1]:
                        if attendance:
                            for each in attendance:
                                print(each.user_id, each.timestamp)
    
                                atten_time = each.timestamp
                                local_tz = pytz.timezone(
                                    self.env.user.partner_id.tz or 'GMT')
                                local_dt = local_tz.localize(atten_time, is_dst=None)
                                utc_dt = local_dt.astimezone(pytz.utc)
                                attendance_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
                                attendance_time = self.convertDate_to_utc(atten_time)
                                atten_time_datetime = datetime.strptime(attendance_time, "%Y-%m-%d %H:%M:%S")
                                atten_date = atten_time_datetime.date()
    
                                if info.date_from <= atten_date <= info.date_to:
                                    attendance_dict[each.user_id].append(atten_time_datetime)
                                    print(each.user_id, '=', atten_time_datetime)
                            for user_id, atten_times in attendance_dict.items():
                                print('==>', user_id, '=', atten_times)
    
                                dates = {}
                                for atten_time in atten_times:
                                    atten_date = atten_time.date()
                                    if atten_date not in dates:
                                        dates[atten_date] = []
                                    dates[atten_date].append(atten_time)
    
                                for atten_date, times in dates.items():
                                    times.sort()
                                    dates[atten_date] = times
    
                                updated_atten_times = [time for times in dates.values() for time in times]
                                updated_atten_times.sort()
                                attendance_dict[user_id] = updated_atten_times
    
                                employee = self.env['hr.employee'].search([('device_id_num', '=', user_id)])
                                print(user_id, '===>', len(employee))
    
                                print(employee_each)
                                if len(employee) == 1:
                                    checkintype = employee.checkintype
                                    shift_id = employee.shift_id
                                    print(employee)
                                    hour_resting = employee.hour_resting
                                    for atten_time in updated_atten_times:
                                        day = datetime.strftime(atten_time, "%d")
                                        print(day)
                                        existing_attendance = zk_attendance.search(
                                            [('device_id_num', '=', user_id)], limit=1)
                                        existing_hr_attendance = hr_attendance.search([('employee_id', '=', employee.id), ('check_out', '=', False)], limit=1)
                                        print('===>', atten_time)
                                        zkuser = self.env['vitouzkf.zk.user'].search(
                                            [('user_id', '=', user_id)],
                                            limit=1)
    
                                        if existing_attendance:
                                            for exist in existing_attendance:
                                                if not exist.check_in == atten_time:
                                                    check_in_atten = zk_attendance.search(
                                                        [('check_in', '=', atten_time),
                                                         ('device_id_num', '=', user_id)])
                                                    check_out_atten = zk_attendance.search(
                                                        [('check_in', '=', atten_time),
                                                         ('device_id_num', '=', user_id)])
                                                    if not check_in_atten:
                                                        zk_attendance.create({
                                                            'employee_id': employee.id,
                                                            'zkuser': zkuser.name,
                                                            'check_in': atten_time,
                                                            'day': day,
                                                            'in_out': '',
                                                            'device_id_num': user_id,
                                                            'devicename': info.name,
                                                            'device_ip': info.device_ip,
                                                            'checkintype': checkintype,
                                                            'hour_resting': hour_resting,
    
                                                        })
    
    
                                        else:
                                            zk_attendance.create({
                                                'employee_id': employee.id,
                                                'zkuser': zkuser.name,
                                                'check_in': atten_time,
                                                'day': day,
                                                'in_out': '',
                                                'device_id_num': user_id,
                                                'devicename': info.name,
                                                'device_ip': info.device_ip,
                                                'checkintype': checkintype,
                                                'hour_resting': hour_resting,
                                            })
                                            print('===>', atten_time)
                                    return self.myinfo("Successful download attendance", "success")
    
                                    self.myinfo("successfull download attendance",'success')
                                    raise ValidationError(_('Successful down load attendance'))
    
    
                                elif len(employee) > 1:
                                    raise ValidationError(
                                        "More Than One Employee Is Found With The Same Device Id" + user_id)
    
                conn_1.disconnect()
                raise UserError(_('Successful down load attendance'))
                return True
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
        else:
            raise UserError(_('Unable to get the attendance log, please'
                              'try again later.'))
    def action_update_inout(self):
        for info in self:
            att_all = self.env['vitouzkf.attendance.all']


            data = att_all.search([('check_in', '>=', info.date_from ), ('check_in', '<=', info.date_to )])
            for rec in data:
                employee = self.env['hr.employee'].search([('device_id_num', '=', rec.device_id_num)])
                checkintype = employee.checkintype
                shift_id = employee.shift_id
                shift2_id = employee.shift2_id
                time_in_base2 =0
                time_out_base2 =0
                in_out = ''
                hour_from_base = 2
                check_in_r = rec.check_in
                check_in_dt =  datetime.strptime(str(rec.check_in), "%Y-%m-%d %H:%M:%S") #rec.check_in.strftime('%Y-%m-%d %H:%M:%S').timestamp
                check_in = self.convertDate(check_in_dt)
                check_in_hm = rec.check_in.strftime('%H:%M')
                check_in_hh = rec.check_in.strftime('%H')
                check_in_mm = rec.check_in.strftime('%M')
                check_in_hh_int = int(check_in_hh)
                check_in_mm_int = float(check_in_mm)/100
                check_in_hh_mm = check_in_hh_int + check_in_mm_int

                my_date_convert = self.convert_date_to_local(check_in_r)

                check_in_date =  rec.check_in.strftime('%Y-%m-%d')
                print(rec.check_in, check_in_hh_mm)
                print(employee)
                if checkintype=='1 time':
                    shift1 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift_id.name)])
                    shift2 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift2_id.name)])
                    time_in_base1 = shift1.shift_in
                    time_out_base1 = shift1.shift_out
                
                    time_in_base2 = shift2.shift_in
                    time_out_base2 = shift2.shift_out
                
                    in_out = 'in'
                else:
                    shift1 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift_id.name)])
                    shift2 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift2_id.name)])
                    time_in_base1 = shift1.shift_in
                    time_out_base1 = shift1.shift_out
                    time_in_base2 = shift2.shift_in
                    time_out_base2 = shift2.shift_out
                    in_out = 'out'

                shift1 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift_id.name)])
                shift2 = self.env['vitouzkf.hs.shifts'].search([('name', '=', shift2_id.name)])
                time_in_base1 = shift1.shift_in
                time_out_base1 = shift1.shift_out
                time_in_base2 = shift2.shift_in
                time_out_base2 = shift2.shift_out

                data.write({
                    'time_in_base1': time_in_base1,
                    'time_out_base1': time_out_base1,
                    'time_in_base2': time_in_base2,
                    'time_out_base2': time_out_base2,


                })

                timestr = time_in_base1.strftime('%H%M')
                hr_base_from_base_in1 = float(time_in_base1)
                hr_base_from_base_in2 = float(time_in_base2)
                hr_base_from_base_out1 = float(time_out_base1)
                hr_base_from_base_out2 = float(time_out_base2)


                checkin_hhmm_f = self.convert_date_to_hhmm(my_date_convert)

                print(checkin_hhmm_f)
                minval =self.MinValue(checkin_hhmm_f, hr_base_from_base_in1,hr_base_from_base_in2, hr_base_from_base_out1, hr_base_from_base_out2)
                print(minval)

                ln = len(minval)
                shift = minval[ln-1:ln]
                if rec.state=='posted':
                    rec.write({
                            'in_out': minval,
                            'shift': int(shift),
                            'check_in_date':check_in_date

                    })

            return self.myinfo("Successfull update attendance",'success')


    def MinValue(self,check_in_hh_mm, hr_base_from_base_in1, hr_base_from_base_in2, hr_base_from_base_out1, hr_base_from_base_out2):
        i =0
        v1= hr_base_from_base_in1
        v2= hr_base_from_base_in2
        v3 = hr_base_from_base_out1
        v4 = hr_base_from_base_out2

        data = []

        data.append({'name': 'hr_base_from_base_in1', 'hm': v1, 'in_out':'in1'})
        data.append({'name': 'hr_base_from_base_in2', 'hm': v2, 'in_out':'in2'})
        data.append({'name': 'hr_base_from_base_out1', 'hm': v3, 'in_out':'out1'})
        data.append({'name': 'hr_base_from_base_out2', 'hm': v4, 'in_out':'out2'})


        print(data)

        idx = self.getnearval(data, check_in_hh_mm )
        return  idx
    def getnearval(self, L, target):
        result = vals.get('order_line')
        desired_id = result[0][2]["tax_id"][0][2][0]
        print(L)
        lst =[];

        for d in L:
            lst.append(d["hm"])

        idx = min(lst, key=lambda x: abs(target-x))

        res = None
        for sub in L:
            if sub['hm'] == idx:
                res = sub
                break

        print(target,'=', idx,'=', res["in_out"])
        return res["in_out"]
    def val1_small(self, val1, val2):
        if val1<val2:
            return True
        else:
            return False

    def convertDate_to_utc(self, check_in):
        atten_time = check_in.timestamp
        local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
        local_dt = local_tz.localize(check_in, is_dst=None)
        utc_dt = local_dt.astimezone(pytz.utc)
        attendance_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
        atten_time_datetime = datetime.strptime(attendance_time, "%Y-%m-%d %H:%M:%S")
        atten_date = atten_time_datetime.date()

        return attendance_time

    def convert_date_to_local(self, date_convert):
        user_tz = self.env.user.tz or pytz.utc
        local = pytz.timezone(user_tz)
        format_data ="%Y-%m-%d %H:%M:%S"
        DEFAULT_SERVER_DATETIME_FORMAT

        display_date_result = datetime.strftime(pytz.utc.localize(datetime.strptime(str(date_convert), format_data)).astimezone(local), format_data)
        return display_date_result
    def convert_date_to_hhmm(self, date_convert):
        hhmm = date_convert.strftime('%H:%M')
        print(date_convert)
        dateteme = self.convert_str_to_datetime(date_convert)

        hh = dateteme.strftime('%H')
        mm = dateteme.strftime('%M')
        hh_int = int(hh)
        mm_int = float(mm) / 60
        hh_mm_int = hh_int + mm_int
        return hh_mm_int
    def convert_str_to_datetime(self, date_str):

        input = "2018-10-09 20.00"
        d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")  # parse to datetime object
        return d

    def action_generate_att(self):
        att_all = self.env['vitouzkf.attendance.all']
        att_hr = self.env['hr.attendance']
        for rec in self:
            datas = att_all.search(
                [('check_in', '>=', rec.date_from), ('check_in', '<=', rec.date_to), ('employee_id', '=', 'admin')],
                order='check_in asc , device_id_num asc')
            datas_in = att_all.search(
                domain=[('check_in', '>=', rec.date_from), ('check_in', '<=', rec.date_to), ('in_out', 'ilike', 'in')],
                order='check_in asc , device_id_num asc')

            datas_out = att_all.search(
                domain=[('check_in', '>=', rec.date_from), ('check_in', '<=', rec.date_to), ('in_out', 'ilike', 'out')],
                order='check_in asc , device_id_num asc')


            for data in datas_in:
                print('==>', data.check_in, '=', data.in_out)
                in_out = data.in_out
                check_in_get = data.check_in
                check_out = data.check_in
                name = data.employee_id.id
                device_id_num = data.device_id_num

                if in_out=='in1':
                    check_in = data.check_in
                    datas_out_att = datas_out.search(domain=[('device_id_num','=',device_id_num), ('check_in_date','=',data.check_in_date), ('in_out','=','out1')], limit=1)
                    if len(datas_out_att)>0:
                        check_out = datas_out_att.check_in

                        att_hr_out = att_hr.search(
                            domain=[('employee_id', '=', name), ('check_in', '=', check_in)])
                        if len(att_hr_out) == 0:
                            att_hr_out.create({
                                'employee_id': name,
                                'check_in': check_in,
                                'check_out': check_out,
                            })

                    else:
                        check_out = None


                if in_out =='in2':

                    check_in = data.check_in
                    datas_out_att = datas_out.search(
                        domain=[('device_id_num', '=', device_id_num), ('check_in_date', '=', data.check_in_date),
                                ('in_out', '=', 'out2')], limit=1)
                    if len(datas_out_att)>0:
                        check_out = datas_out_att.check_in

                        att_hr_out = att_hr.search(
                            domain=[('employee_id', '=', name), ('check_in', '=', check_in)])
                        if len(att_hr_out) == 0:
                            att_hr_out.create({
                                'employee_id': name,
                                'check_in': check_in,
                                'check_out': check_out,
                            })

                    else:
                        check_out = None


                print(name, '=', '=', data.employee_id.name, data.day, '=', data.check_in, '=', check_out)

                att_hr_out = att_hr.search(
                    domain=[('employee_id', '=', name), ('check_in', '=', check_in)])
                if len(att_hr_out) == 0:
                    att_hr_out.create({
                        'employee_id': name,
                        'check_in': check_in,
                        'check_out': check_out,
                    })
                print(name, '=', data.employee_id.name, data.day, '=', data.check_in, '=', check_out)

            return self.myinfo('Successul generate attendance','success')





    def action_download_zk_user(self):
        zk_attendance_user = self.env['vitouzkf.zk.user']
        hr_attendance = self.env['hr.attendance']
        for info in self:
            machine_ip = info.device_ip
            zk_port_1 = info.port_number

            try:
                # Connecting with the device with the ip and port provided
                zk_1 = ZK(machine_ip, port=zk_port_1, timeout=30,
                          password=0,
                          force_udp=False, ommit_ping=False)

            except NameError:
                raise UserError(
                    _("Pyzk module not Found. Please install it"
                      "with 'pip3 install pyzk'."))
            conn_1 = self.device_connect(zk_1)

            if conn_1:
                conn_1.disable_device()

                users = conn_1.get_users()

                user = conn_1.get_users()
                print('users=', users)


                if users:
                    user_dict = defaultdict(list)
                    for User in users:
                        print(User)
                        userExist = zk_attendance_user.search([('name', '=', User.name),('user_id', '=', User.user_id),('devicename', '=', info.name)])
                        if len(userExist)==0:
                            userExist.create({
                                'name': User.name,
                                'uid': User.uid,
                                'user_id': User.user_id,
                                'devicename': info.name,
                                'device_id': info.id,
                                'device_ip': info.device_ip,
                            })
                        else:

                            userExist.write({
                                'uid': User.uid,
                                'user_id': User.user_id,
                                'devicename': info.name,
                                'device_id': info.id,
                                'device_ip': info.device_ip,

                            })
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'message': 'Successfull download users',
                            'type': 'success',
                            'sticky': False
                        }
                    }


                conn_1.disconnect()
                raise UserError(_('Successful down load attendance'))
                return True
            else:
                raise UserError(_('Unable to connect, please check the parameters and network connections.'))
        else:
            raise UserError(_('Unable to get the attendance log, please'
                              'try again later.'))
    def myinfo(self, message, infotype):
        # /'success', 'info', 'warning'
        for rec in self:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': message,
                    'type': infotype,
                    'sticky': False
                }
            }


