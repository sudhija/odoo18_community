
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



class VitouSlotColor(models.Model):
    _name = 'vitouzkf.color'
    _description = "Color"
    def get_color_by_state(self, state):
        color_state1 = 'danger' #done, closed
        color_state2 = 'warning' #voided, rejected
        color_state3 = 'info' #other
        color_state4 = 'secondary' #draft
        color_state8 = 'primary' #approved
        color_state10 = 'success' #posted, requested, opened

        color_text1 = 'text-danger'
        color_text2 = 'text-warning'
        color_text3 = 'text-info'
        color_text4 = 'text-secondary'
        color_text8 = 'text-primary'
        color_text10 = 'text-success'


        color = []
        if state == 'done' or state=='closed':
            color = self.set_color(1,color_state1,color_text1)
        elif state == 'voided' or state == 'rejected':
            color = self.set_color(2,color_state2,color_text2)
        elif state == 'draft':
            color = self.set_color(4,color_state4,color_text4)
        elif state == 'approved':
            color = self.set_color(8,color_state8,color_text8)
        elif state == 'posted' or state == 'requested' or state == 'opened':
            color = self.set_color(10,color_state10,color_text10)
        else:
            color = self.set_color(3,color_state3,color_text3)

        return color

    def set_color(self, code, color_state, color_text):
        color = [
            {'color_code': code,
             'color_state': color_state,
             'color_text': color_text, }
        ]
        return color


    """
        code = 1 , Red 		=> danger       => done
        code = 2 , Orange 	=> warning      => void, rejected
        code = 3 , Yellow 	=> info         => other
        code = 4 , Light blue 	=> secondary=> draft
        code = 5 , Dark purple
        code = 6 , Salmon pink
        code = 7 , Medium blue
        code = 8 , Dark blue	=> primary  => approved
        code = 9 , Fushia
        code = 10 , Green 	=> success      => posted, requested
        code = 11 , Purple
    """