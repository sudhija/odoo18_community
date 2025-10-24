# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import fields, models, tools


class DailyAttendance(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'vitouzkf.daily.attendance'
    _description = 'Daily Attendance Report'
    _auto = False
    _order = 'punching_day desc'

    employee_id = fields.Many2one('hr.employee', string='Employee',
                                  help='Employee Name')
    device_id_num = fields.Char(string="Password")
    punching_day = fields.Datetime(string='Date', help='Date of punching')
    check_in = fields.Datetime(string='Check In')
    check_out = fields.Datetime(string='Check Out')
    i_check = fields.Char(string="Check Type")
    o_check = fields.Char(string="Check Type")
    is_danger = fields.Boolean(default=True)

    def init(self):
        """Retrieve the data's for attendance report"""
        tools.drop_view_if_exists(self._cr, 'vitouzk_daily_attendance')
        # Use hr_attendance as the source (controller creates hr.attendance records)
        # and provide safe defaults for module-specific columns that may not exist.
        query = """
            CREATE OR REPLACE VIEW vitouzk_daily_attendance AS (
                SELECT
                    MIN(ha.id) AS id,
                    ha.employee_id AS employee_id,
                    ha.write_date AS punching_day,
                    ''::text AS device_id_num,
                    ha.check_in AS check_in,
                    ha.check_out AS check_out,
                    ''::text AS i_check,
                    ''::text AS o_check,
                    false AS is_danger
                FROM hr_attendance ha
                JOIN hr_employee e ON (ha.employee_id = e.id)
                GROUP BY
                    ha.employee_id,
                    ha.write_date,
                    ha.check_in,
                    ha.check_out
            )
        """
