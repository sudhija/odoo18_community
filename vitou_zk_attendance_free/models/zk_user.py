# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import api, fields, models
from .lic.globals import func_mod, msg_sep


class ZkMachineMachine(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'vitouzkf.zk.user'
    _description = 'Fingerprint user'
    _inherit = 'mail.thread'

    @api.constrains('check_in', 'check_out', 'employee_id')
    def _check_validity(self):
        """Overriding the __check_validity function for employee attendance."""
        pass

    name = fields.Char(string="Employee", required=True)
    uid = fields.Integer(string="Uid")
    user_id = fields.Integer(string="ZK User")

    device_id = fields.Many2one(comodel_name='vitouzkf.set.device', string="Device ID", store=True)
    devicename = fields.Char(string="Device Name", related='device_id.name', store=True)
    device_ip = fields.Char(string="Device IP", related='device_id.device_ip', store=True)


    state = fields.Selection(
        string="State",
        selection=[
            ('posted', 'Posted'),
            ('done', 'Done'),
        ], default="posted", required=True
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
    date_register = fields.Datetime(string='Date Register', default=None)

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
