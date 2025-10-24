
# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82
#
###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError



class VitouSlotVariable(models.Model):
    _name = 'vitouzkf.variable'
    _description = "variable"

    # def leading_zero(self, value, digit):
    #     f = "{:0" + digit + "d}"
    #     # print(f)
    #     # return "{:09d}".format(value)
    #     return f.format(value)