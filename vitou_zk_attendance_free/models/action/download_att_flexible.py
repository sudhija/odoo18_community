# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82
#
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

import datetime
from ..lic.globals import func_mod
from datetime import datetime, timedelta, time
from collections import defaultdict
import pytz



try:
     from zk import ZK, const
except ImportError as e:
     raise ValidationError(_(e.message))


class VitouzkDownloadAttFlexible(models.TransientModel):
     _name = 'vitouzkf.download.att.flexible'
     _description = 'Download Staff Attendance Flexible'
     #_inherit = ['mail.thread']
     #_rec_name = "provider"
     # _sql_constraints = [
     #      ('name_unique', 'unique(name)', "Currency Code is duplicated!"),
     # ]




     # date = fields.Date(string="OpertionDay", required=True)
     device_id = fields.Many2one(comodel_name='vitouzkf.set.device', string='Device Id', required=True)
     device_name = fields.Char(string='Device Name', related='device_id.name')
     device_ip = fields.Char(string='Device IP', related='device_id.device_ip')
     port_number = fields.Integer(string='Port No', related='device_id.port_number')
     company_id = fields.Many2one(string='Company Id', related='device_id.company_id')
     date_from = fields.Date(string="Date From", default=fields.Date.today())
     date_to = fields.Date(string="Date To", default=fields.Date.today())



     def action_download_att(self):
          # print('donwload...')
          return self.env[func_mod].myinfo('Downloading...', 'success')

     def action_test_connection(self):
          """Checking the connection status"""
          success_ports = []
          error_ports = []
          for rec in self:
               if rec.port_number:
                    device_ip = rec.device_ip
                    port = rec.port_number
                    # print('device=',device_ip, ', port=', port )
                    zk_1 = ZK(device_ip, port=port, timeout=30,
                              password=False, ommit_ping=False)
               try:
                    if zk_1.connect():
                         msg = 'Successful connect to device on port ' + str(rec.port_number)
                         return self.info(msg, 'success')

                         # success_ports.append(self.port_number)

                    else:
                         msg = 'Fail connect to device on port ' + str(rec.port_number)
                         return self.info(msg, 'warning')
                         # error_ports.append(self.port_number)
               except Exception as e:
                    msg = 'Error connect to device on port ' + str(rec.port_number) + ',=>' + e.message
                    return self.info(msg, 'danger' )
                    # error_ports.append(self.port_number)

     def device_connect(self, zk):
          """Function for connecting the device with Odoo"""
          try:
               conn = zk.connect()
               return conn
          except Exception:
               return False

     def action_download_attendance(self):
          """Function to download attendance records from the device"""
          # if (self.lic_check()):
          self.env[func_mod].is_my_saft()
          zk_attendance = self.env['vitouzkf.attendance.all.flexible']
          hr_attendance = self.env['hr.attendance']
          for info in self:
               machine_ip = info.device_ip
               zk_port_1 = info.port_number
               # zk_port_2 = info.port_number2
               # zk_port_5 = info.port_number3
               try:
                    # Connecting with the device with the ip and port provided
                    zk_1 = ZK(machine_ip, port=zk_port_1, timeout=30,
                              password=0,
                              force_udp=False, ommit_ping=False)
                    # zk_2 = ZK(machine_ip, port=zk_port_2, timeout=30,
                    #           password=0,
                    #           force_udp=False, ommit_ping=False)
                    # zk_3 = ZK(machine_ip, port=zk_port_5, timeout=30,
                    #           password=0,
                    #           force_udp=False, ommit_ping=False)
               except NameError:
                    raise ValidationError(
                         _("Pyzk module not Found. Please install it"
                           "with 'pip3 install pyzk'."))
               conn_1 = self.device_connect(zk_1)
               # conn_2 = self.device_connect(zk_2)
               # conn_5 = self.device_connect(zk_3)
               if conn_1:
                    conn_1.disable_device()

                    attendance_1 = conn_1.get_attendance()

                    conn_1.enable_device()
                    conn_1.disconnect()

                    # log = attendance_1[0]
                    # print({
                    #      'uid': log.uid,  # User’s machine ID (int)
                    #      'timestamp': log.timestamp,  # datetime.datetime in local tz
                    #      'punch': log.punch,  # 0=check-out, 1=check-in
                    #      # 'status': log.status,  # machine-specific status code
                    #      # 'verify_method': log.verify_method,  # e.g. fingerprint, password
                    #      # 'work_code': log.work_code,  # custom work codes if enabled
                    # })

                    if attendance_1:
                         attendance_dict = defaultdict(list)
                         # print('=====',attendance_1 )


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
                                        if info.date_from <= atten_date <= info.date_to:
                                             attendance_dict[each.user_id].append(atten_time_datetime)
                                             # attendance_dict[each.user_id].append({'datetime':atten_time_datetime,'punch':each.punch})

                         # print('all=', attendance_dict.items())

                         for user_id, atten_times in attendance_dict.items():
                              dates = {}

                              for atten_time in atten_times:
                                   # print('==', atten_time)
                                   atten_date = atten_time.date()
                                   if atten_date not in dates:
                                        dates[atten_date] = []
                                   dates[atten_date].append(atten_time)


                              updated_atten_times = [time for times in dates.values() for time in times]
                              updated_atten_times.sort()
                              attendance_dict[user_id] = updated_atten_times

                              # for atten_time in atten_times:
                              #      print('==', user_id ,', ', atten_time['datetime'],', ', atten_time['punch'])

                              employee = self.env['hr.employee'].sudo().search([('zkuser_user_id', '=', user_id),('zk_isfixshift','=',False)],limit=1)

                              zkuser_search = self.env['vitouzkf.zk.user'].sudo().search([('user_id','=',user_id)])



                              if employee:
                                   for atten_time in updated_atten_times:
                                        existing_attendance = zk_attendance.sudo().search(
                                             [('zkuser', '=', user_id), ('check_in', '=', atten_time )], limit=1)
                                        # existing_hr_attendance = hr_attendance.search(
                                        #      [('employee_id', '=', employee.id), ('check_in', '=', atten_time)], limit=1)
                                        # print('att=', existing_attendance)
                                        day = datetime.strftime(atten_time, "%d")
                                        if len(existing_attendance)<=0:
                                             # print('kuser=', user_id, ', emp=', employee.id, ',date=', atten_time, ',deviceid=', info.device_id.id)
                                             zk_attendance.create({
                                                  'zkuser': user_id,
                                                  'zkusername': zkuser_search.name,
                                                  'employee_id': employee.id,
                                                  'check_in': atten_time,
                                                  'day': day,
                                                  'device_id_num':  info.device_id.id,
                                                  'devicename': info.device_name ,
                                                  'device_ip': info.device_ip,
                                                  'state_att':'download'
                                             })


                    return self.info('Successful download', 'success')

               else:
                    raise UserError(_('Unable to connect, please check the parameters and network connections.'))
          else:
               raise UserError(_('Unable to get the attendance log, please'
                                 'try again later.'))

          # conn_1.enable_device()
          # conn_1.disconnect()

     def info(self,info, type):
          return self.env[func_mod].myinfo(info, type)

     def action_reload(self):
          self.env[func_mod].reload()

     # def action_close(self):
     #      # This special action tells the client to close the popup
     #      return {'type': 'ir.actions.act_window_close'}

