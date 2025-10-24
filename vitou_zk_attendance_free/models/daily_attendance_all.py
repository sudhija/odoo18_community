# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from .lic.globals import func_mod
from datetime import date

from odoo.tools import date_utils
from odoo.fields import Date

from datetime import datetime, date, timedelta, time
import pytz

from itertools import groupby

class ZkMachineAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'vitouzkf.attendance.all'
    _description = 'Attendance All'
    _inherit = 'hr.attendance'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """Overriding the __check_validity function for employee attendance."""
        pass


    employee_id = fields.Many2one(comodel_name='hr.employee', string="Employee ID", store=True, domain=[('zk_isfixshift','=',True)])
    employee_name = fields.Char(string='Employee Name', related='employee_id.name', store=True)
    zk_isfixshift = fields.Boolean(related='employee_id.zk_isfixshift', store=True)
    zkuser_id = fields.Many2one(comodel_name='vitouzkf.zk.user', store=True)
    zkuser = fields.Integer(related='employee_id.zkuser_user_id', string="User ID", store=True)
    zkusername=fields.Char( related='employee_id.zkuser_user_name', string="User Name", store=True)
    department_id = fields.Many2one(related='employee_id.department_id', string='Department', store=True)

    position_id = fields.Many2one(related='employee_id.job_id', string='Position', store=True)
    company_id = fields.Many2one(related='employee_id.company_id', string='Company', store=True)

    device_id = fields.Many2one(comodel_name='vitouzkf.set.device', string='Device ID', help="The ID of the Biometric Device", store=True)
    device_id_num = fields.Integer(related='device_id.id', string='Biometric Device ID',
                                    help="The ID of the Biometric Device", store=True)
    devicename = fields.Char(related='device_id.name', string="Device Name", store=True)
    device_ip = fields.Char(related='device_id.device_ip', string="Device IP", store=True)

    device_in_out = fields.Selection(related='device_id.device_in_out',
        string="Device In_Out",  store=True
    )


    device_id_num_id = fields.Many2one(comodel_name='vitouzkf.set.device', string='Device ID', help="The ID of the Biometric Device")
    date_inout = fields.Date(string='Date InOut', default=None,compute='_update_day', store=True)
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out', default=None)
    # Flags used by the import/download flow to mark in/out records
    i_check = fields.Char(string='I Check', help='Inbound check marker')
    o_check = fields.Char(string='O Check', help='Outbound check marker')

    work_hour = fields.Float( widget='float_time', string="Work Hour", default=0.00)
    rest_hour = fields.Float(related='employee_id.rest_hour', widget='float_time', string="Rest Hour", store=True)
    total_work_hour = fields.Float(widget='float_time', string="Total Work Hour", store=True, default=0.00, compute='_update_total_work_hour')
    is_att = fields.Boolean( string='Is Att.', default=None)
    for_att = fields.Selection(
        string='For Att',
        selection=[
            ('yes', 'Yes'),
            ('no', 'No')
        ], default='no', required=True
    )

    check_in_date = fields.Datetime(string='Check In Date')
    day = fields.Integer(string='Day', compute='_update_day', store=True)
    checkin_shift_id = fields.Many2one(comodel_name='vitouzkf.hs.shifts', string='Checkin Shift')
    is_same_day = fields.Boolean(related='checkin_shift_id.is_same_day', string='Is Same Day', store=True)

    punching_time = fields.Datetime(string='Punching Time',
                                    help="Punching time in the device")
    in_out = fields.Selection(string="In-Out",
                            selection=[
                                ('in1','in1'),
                                ('out1','out1'),
                                ('in2','in2'),
                                ('out2','out2'),

                            ], default=None)


    is_danger = fields.Boolean(default=True)

    state = fields.Selection(
        string="State",
        selection=[
            ('posted', 'Posted'),
            ('done', 'Done'),
            ('voided','Voided')
        ], default="posted", required=True
    )
    state_att = fields.Selection(
        string="State Att",
        selection=[
            ('posted', 'Posted'),
            ('download', 'Download'),
        ], default="posted", required=True
    )



    checkintype = fields.Selection(related='employee_id.checkintype', string="Checkin Type", store=True)
    shift_id = fields.Many2one( related='employee_id.shift_id', string="Time Shift", store=True)
    shift2_id = fields.Many2one(related='employee_id.shift2_id', string="Time Shift2", store=True)

    time_in_base1 = fields.Float(related='employee_id.shift_id.shift_in', widget='float_time', string="Time In B1", help="Time In Base1 Must be 24 hours format", store=True)
    time_out_base1 = fields.Float(related='employee_id.shift_id.shift_out', widget='float_time', string="Time Out B1", help="Time Out Base1 Must be 24 hours format", store=True)

    time_in_base2 = fields.Float(related='employee_id.shift2_id.shift_in',widget='float_time', string="Time In B2" ,help="Time Im Base1  Must be 24 hours format", store=True)
    time_out_base2 = fields.Float(related='employee_id.shift2_id.shift_out', widget='float_time', string="Time Out B2" ,help="Time Out Base2 Must be 24 hours format", store=True)

    early_or_late = fields.Char(string='Early-Late')
    early_or_late_h = fields.Float(string='Early-Late Hrs', widget='float_time', default=0)

    status_vitouzk = fields.Selection(
        related='employee_id.status_vitouzk', string='Staff Status', default='Active', store=True
    )





    done_uid = fields.Many2one(comodel_name='res.users', string="Done UID")
    done_uname = fields.Char(related='done_uid.name', string='Done UName')
    done_staff = fields.Char(string='Done Staff')
    done_date = fields.Char(string="Done Date")

    undodone_uid = fields.Many2one(comodel_name='res.users', string="Undo Done UID")
    undodone_uname = fields.Char(related='done_uid.name', string='Undo Done UName')
    undodone_staff = fields.Char(string='Undo Done Staff')
    undodone_date = fields.Char(string="Undo Done Date")

    voided_uid = fields.Many2one(comodel_name='res.users',string="Voided UID")
    voided_uname = fields.Char(related='done_uid.name', string='Voidede UName')
    voided_staff = fields.Char(string='Voided Staff')
    voided_date = fields.Char(string="Voided Date")

    unvoided_uid = fields.Many2one(comodel_name='res.users', string="Unvoided UID")
    unvoided_uname = fields.Char(related='done_uid.name', string='Unvoided UName')
    unvoided_staff = fields.Char(string='Unvoided Staff')
    unvoided_date = fields.Char(string="Unvoided Date")

    @api.model
    def _get_view_cache_key(self, view_id=None, view_type='tree', **options):
        # add something unique per user or per session

        key = super()._get_view_cache_key(view_id, view_type, **options)
        return key + (self.env.uid,)

    @api.model
    def _get_view(self, view_id=None, view_type='tree', **options):
        print('load.....')
        arch, view = super()._get_view(view_id, view_type, **options)
        return arch, view





    def action_gen_in_out(self):
        hr_mod = self.env['hr.attendance']
        att_mod = self.env['vitouzkf.attendance.all']
        self.action_update_inout()



    def info(self, message, type):
        print('yyyy')
        return self.env[func_mod].myinfo(message, type)

    def unlink(self):
         for rec in self:
              domain = [('type_id', '=', rec.id)]
              found = self.env['ittechnician.type'].sudo().search(domain)
              if rec.state =='done':
                   raise ValidationError(_('Cannot delete for state was done!'))
              return super().unlink()

    @api.depends('work_hour')
    def _update_total_work_hour(self):
        for rec in self:
            work_hour = rec.work_hour
            rest_hour = rec.rest_hour
            total_work_hour = work_hour - rest_hour
            print('twh=', total_work_hour)
            if rec.state == 'posted':
                if work_hour>0:
                    rec.total_work_hour = total_work_hour
                else:
                    rec.total_work_hour = 0.0

    @api.depends('check_in')
    def _update_day(self):
        for rec in self:
            fun_mod_name = self.env[func_mod]
            if rec.state == 'posted':
                if rec.check_in:
                    check_in = fields.Datetime.from_string(rec.check_in)
                    check_in_utc = fields.Datetime.from_string(fun_mod_name.convert_date_to_local(check_in))
                    day = check_in_utc.strftime("%d")
                    date_inout = check_in_utc.strftime('%Y-%m-%d')
                    rec.day = day
                    rec.date_inout = date_inout
                else:
                    rec.day = None
                    rec.date_inout = None




    def action_void(self):
        for rec in self:
            if rec.state == 'posted':
                rec.state = 'voided'
                rec.voided_uid = self.get_uid()
                rec.voided_staff = self.get_staff()
                rec.voided_date = self.get_date()
                rec.in_out: ''
                rec.checkin_shift_id = None
                rec.early_or_late = None
                rec.early_or_late_h = 0.0
                rec.check_out = None
                rec.is_att = None
                rec.for_att = 'no'

            else:
                return self.info('Invalid state','warning')
    def action_unvoid(self):
        for rec in self:
            if rec.state == 'voided':
                rec.state = 'posted'
                rec.unvoided_uid = self.get_uid()
                rec.unvoided_staff = self.get_staff()
                rec.unvoided_date = self.get_date()
            else:
                return self.info('Invalid state','warning')

    def action_done(self):
        for rec in self:
            if rec.state == 'posted':
                rec.state = 'done'
                rec.done_uid = self.get_uid()
                rec.done_staff = self.get_staff()
                rec.done_date = self.get_date()
            else:
                return self.info('Invalid state','warning')
    def action_undodone(self):
        for rec in self:
            if rec.state == 'done':
                rec.state = 'posted'
                rec.undodone_uid = self.get_uid()
                rec.undodone_staff = self.get_staff()
                rec.undodone_date = self.get_date()
            else:
                return self.info('Invalid state','warning')
    def action_update_inout(self):
        raise ValidationError(_("This function is available in paid version!!"))
        return self.env[func_mod].myinfo("Successfull update attendance",'success')

    def action_reset(self):
        for rec in self:
            if rec.state == 'posted':
                rec.voided_uid = self.get_uid()
                rec.voided_staff = self.get_staff()
                rec.voided_date = self.get_date()
                rec.in_out: ''
                rec.checkin_shift_id = None
                rec.early_or_late = None
                rec.early_or_late_h = 0.0
                rec.check_out = None
                rec.is_att = None
                rec.for_att = 'no'
            else:
                return self.info('Invalide state!', 'warning')


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


    """/////////////////////////"""



    def get_uid(self):
        return self.env.user.id

    def get_uname(self):
        return self.env.user.login

    def get_date(self):
        return fields.Datetime.now()

    def get_staff(self):
        return self.env[func_mod].get_staff(self.get_uid())



    def action_download_att(self):
        # print('open form')
        model = 'vitouzkf.set.device'
        return self.env[func_mod].open_new_form('Device',model, 'vitou_zk_attendance_free.view_vitouzk_vitouzk_download_att_form', 'form', 'new');

    def action_reload(self):
        # print('xxxx====')
        self.env[func_mod].reload()

    def get_start_day(self):
        today = Date.today()
        start_date, end_date = date_utils.get_month(today)
        return start_date

    def get_end_day(self):
        today = Date.today()
        start_date, end_date = date_utils.get_month(today)
        return end_date

    def get_today(self):
        return date.today()
