# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################


from odoo import fields, models


class HrEmployee(models.Model):
    """Inherit the model to add field"""
    _inherit = 'hr.employee'

    zkuser_id = fields.Many2one(comodel_name='vitouzkf.zk.user', string='ZK User Id', help="Give the biometric device id", store=True)
    zkuser_user_id = fields.Integer(related='zkuser_id.user_id', string='ZkUser User Id', help="Give the biometric device id", store=True)
    zkuser_user_name = fields.Char(related='zkuser_id.name', string='Zk User Name', help="Give the biometric device id", store=True)

    checkintype = fields.Selection(
          string="Checkin Type",
          selection=[
               ('1 time', '1 time'),
               ('2 times', '2 times'),
          ], default="1 time", required=True, store=True)
    shift_id = fields.Many2one('vitouzkf.hs.shifts', string="Time Shift", store=True)
    shift2_id = fields.Many2one('vitouzkf.hs.shifts', string="Time Shift2", store=True)
    shift3_id = fields.Many2one('vitouzkf.hs.shifts', string="Time Shift3", store=True)
    shift4_id = fields.Many2one('vitouzkf.hs.shifts', string="Time Shift4", store=True)
    rest_hour = fields.Float(string='Resting Hours', widget='float_time', help=' hour and minute, hour:minute')
    zk_isfixshift = fields.Boolean(string='Is Fix Shift', default=True)
    status_vitouzk = fields.Selection(
        [
            ('Intern', 'Intern'),
            ('Probation', 'Probation'),
            ('Active','Active'),
            ('Resigned','Resigned'),
            ('Abandoned','Abandoned'),
            ('Terminated','Terminated'),
            ('Retired','Retired'),
            ('Suspended','Suspended'),

        ], string='Staff Status', required=True, default='Active', store=True
    )

    date_end_vitouzk = fields.Datetime(string='Date End', default=None)



