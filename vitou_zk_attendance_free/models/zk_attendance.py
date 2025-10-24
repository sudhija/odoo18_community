# -*- coding: utf-8 -*-
from odoo import fields,models

class ZkAttendance(models.Model):
    _name = 'zk.attendance'
    _description = 'ZKTeco Attendance Log'

    employee_id = fields.Many2one('hr.employee', string='Employee')
    device_sn = fields.Char(string='Device Serial')
    punch_time = fields.Datetime(string='Punch Time', required=True)
    punch_type = fields.Selection([('in', 'Check In'), ('out', 'Check Out')])