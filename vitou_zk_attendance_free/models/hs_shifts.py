# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import models, api, fields
from .lic.globals import func_mod


class HsShifts(models.Model):
    _name = 'vitouzkf.hs.shifts'
    _description = "Timing Shifts"

    name = fields.Char(string="Shift Name")
    shift_in = fields.Float(string="Shift Time-In" , default=0.0,  help='Shift In as float (e.g. 1.5 = 1h30)')
    shift_out = fields.Float(string="Shift Time-Out",  default=0.0,  help='Shift Out as float (e.g. 1.5 = 1h30)')
    active = fields.Boolean(string="Status", default=True)
    work_hour = fields.Float(string='Work Hour', widget='float_time', compute='_compute_work_hour')
    rest_hours = fields.Float(string='Resting Hours',widget='float_time')

    state = fields.Selection(
        string='State',
        selection=[
            ('posted','Posted'),
            ('done','Done')
        ], default='posted', required=True
    )
    is_same_day = fields.Boolean(string='Is Same Day', default=True, store=True, compute='_compute_work_hour')

    done_uid = fields.Integer(string="Done UID")
    done_uname = fields.Char(string='Done UName')
    done_staff = fields.Char(string='Done Staff')
    done_date = fields.Char(string="Done Date")


    undodone_uid = fields.Integer(string="Undo Done UID")
    undodone_uname = fields.Char(string='Undo Done UName')
    undodone_staff = fields.Char(string='Undo Done Staff')
    undodone_date = fields.Char(string="Undo Done Date")

    @api.depends('shift_in','shift_out')
    def _compute_work_hour(self):
        for rec in self:

            if rec.shift_in and rec.shift_out:
                h_in = rec.shift_in
                h_out = rec.shift_out
                work_hour =  h_out - h_in
                if h_out>h_in:
                    work_hour = h_out - h_in
                    rec.is_same_day = True
                else:
                    work_hour = 24-h_in+h_out
                    rec.is_same_day = False


                rec.work_hour = work_hour

    def action_done(self):
        for rec in self:
            if rec.state =='posted':
                rec.state = 'done'
                rec.done_uid = self.get_uid()
                rec.done_uname = self.get_uname()
                rec.done_staff  = self.get_staff()
                rec.done_date = self.get_date()
            else:
                raise UserWarning('Invalid State!')
    def action_undodone(self):
        for rec in self:
            if rec.state =='done':
                rec.state = 'posted'
                rec.undodone_uid = self.get_uid()
                rec.undodone_uname = self.get_uname()
                rec.undodone_staff  = self.get_staff()
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
