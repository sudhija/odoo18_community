
# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import api, fields, models,_
from cryptography.fernet import Fernet

from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import datetime


class VitouSlotDeveloper(models.Model):
    """Model to hold data from the biometric device"""
    _name = 'vitouzkf.developer'
    # _inherit = ['mail.thread']
    _description = 'Developer'
    #_inherit = 'hr.attendance'
    _sql_constraints = [
         ('name_unique', 'unique(name)', "Provider is duplicated!"),
    ]

    # @api.constrains('check_in', 'check_out', 'employee_id')
    # def _check_validity(self):
    #     """Overriding the __check_validity function for employee attendance."""
    #     pass



    name = fields.Char(string="Developer",default='REAM VITOU', required=True)
    email = fields.Char(string="Email", default='reamvitou@yahoo.com')
    telephone = fields.Char(string="Telephone", default='+855 17 82 66 82')

    # @api.model_create_multi
    # def create(self, vals_list):
    #     # print("reference==", vals_list)
    #     for vals in vals_list:
    #         if not vals.get('reference') or vals['reference'] == 'New':
    #             vals['reference'] = self.env['ir.sequence'].next_by_code('ittechnician.machine')
    #     return super().create(vals_list)







