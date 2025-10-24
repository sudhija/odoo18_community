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
from ..lic.globals import func_mod, msg_sep
from datetime import datetime, timedelta, time
from collections import defaultdict
import pytz


try:
     from zk import ZK, const
except ImportError as e:
     raise ValidationError(_(e.message))


class VitouzkActionDoneAttFix(models.TransientModel):
     _name = 'vitouzkf.done.att.fix'
     _description = 'Done Attendance Fix Shift'
     #_inherit = ['mail.thread']
     #_rec_name = "provider"
     # _sql_constraints = [
     #      ('name_unique', 'unique(name)', "Currency Code is duplicated!"),
     # ]


     date_from = fields.Date(string="Date From", default=fields.Date.today())
     date_to = fields.Date(string="Date To", default=fields.Date.today())
     # department_id = fields.Many2one(comodel_name='hr.employee', string='Department')
     # staff_id = fields.Many2one(comodel_name='hr.employee', string='Staff')





     def action_done(self):
          att_mod = self.env['vitouzkf.attendance.all']
          for rec in self:
               date_from = rec.date_from
               date_to = rec.date_to
               att_get = att_mod.sudo().search(
                    [('state', '=', 'posted'), ('check_in', '>=', date_from.strftime('%Y-%m-%d')),
                     ('check_in', '<=', date_to.strftime('%Y-%m-%d 23:59:59'))], order='check_in asc')

               if not att_get:
                    return self.info('Nothing to apply done!', 'warning')

               att_get.write({
                    'state': 'done',
                    'done_uid': self.get_uid(),
                    'done_date': self.get_date(),
                    'done_staff': self.get_staff()
               })

               return self.info('Successful apply done', 'success')

     def action_undodone(self):
          att_mod = self.env['vitouzkf.attendance.all']
          for rec in self:
               date_from = rec.date_from
               date_to = rec.date_to
               att_get = att_mod.sudo().search(
                    [('state', '=', 'done'), ('check_in', '>=', date_from.strftime('%Y-%m-%d')),
                     ('check_in', '<=', date_to.strftime('%Y-%m-%d 23:59:59'))], order='check_in asc')

               if not att_get:
                    return self.info('Nothing to apply reset to post!', 'warning')

               att_get.write({
                    'state': 'posted',
                    'undodone_uid': self.get_uid(),
                    'undodone_date': self.get_date(),
                    'undodone_staff': self.get_staff()
               })

               return self.info('Successful apply reset to post', 'success')





     def get_uid(self):
          return self.env.user.id

     def get_staff(self):
          return self.env[func_mod].get_staff(self.env.user.id)

     def get_date(self):
          return fields.Datetime.now()

     def get_uid(self):
          return self.env.user.id

     def info(self,info, type):
          return self.env[func_mod].myinfo(info, type)

     def action_reload(self):
          self.env[func_mod].reload()

     def action_close(self):
          self.env[func_mod].close_popup()

