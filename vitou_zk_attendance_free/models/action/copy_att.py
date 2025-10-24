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


class VitouzkActionCopyAtt(models.TransientModel):
     _name = 'vitouzkf.copy.att'
     _description = 'Copy Att to HR Att'
     #_inherit = ['mail.thread']
     #_rec_name = "provider"
     # _sql_constraints = [
     #      ('name_unique', 'unique(name)', "Currency Code is duplicated!"),
     # ]


     date_from = fields.Date(string="Date From", default=fields.Date.today())
     date_to = fields.Date(string="Date To", default=fields.Date.today())
     # department_id = fields.Many2one(comodel_name='hr.employee', string='Department')
     # staff_id = fields.Many2one(comodel_name='hr.employee', string='Staff')





     def action_copy(self):
          # print('donwload...')
          self.env[func_mod].is_my_saft()
          att_mod = self.env['vitouzkf.attendance.all']
          hr_mod = self.env['hr.attendance']
          for rec in self:
               date_from = rec.date_from
               date_to = rec.date_to

               att_get = att_mod.sudo().search(
                    [('state', '=', 'done'), ('is_att', '=', True), ('check_in', '>=', date_from.strftime('%Y-%m-%d')),
                     ('check_in', '<=', date_to.strftime('%Y-%m-%d 23:59:59'))], order='check_in asc')

               if not att_get:
                    return self.info('Nothing to copy', 'warning')


               # print('att=', att_get)

               for att in att_get:
                    employee_id = att.employee_id.id
                    check_in = fields.Datetime.from_string(att.check_in)
                    check_out = fields.Datetime.from_string(att.check_out)
                    zkuser = att.employee_id.zkuser_user_id
                    zkusername = att.employee_id.zkuser_user_name
                    zk_device_id = att.device_id_num.id
                    zk_state_att = att.state_att

                    hr_att = hr_mod.sudo().search([('employee_id','=',employee_id),('check_in','=', check_in)])
                    hr_att_all = hr_mod.sudo()

                    if len(hr_att) == 0:

                         try:

                              hr_att_all.create({
                                   'employee_id':employee_id,
                                   'check_in': check_in,
                                   'check_out': check_out,
                                   'zkuser': zkuser,
                                   'zkusername':zkusername,
                                   'zk_device_id': zk_device_id,
                                   'zk_state_att':zk_state_att

                              })



                         except Exception as e:
                              print(e)

               return self.info('Successful copy', 'success')




     # domain = "[('check_in', '&gt;=', context_today().strftime('%Y-%m-%d')), ('check_in', '&lt;=', context_today().strftime('%Y-%m-%d 23:59:59'))]"


     # def copy_att(self, date_from,date_to):
     #      att_mod = self.env['vitouzkf.attendance.all']
     #      hr_mod = self.env['hr.attendance']
     #
     #      att_get = att_mod.sudo().search([('state', '=', 'done'), ('is_att', '=', True), ('check_in','>=', date_from.strftime('%Y-%m-%d')), ('check_in','<=', date_to.strftime('%Y-%m-%d 23:59:59'))])
     #
     #      print('att=', att_get)
     #      if len(att_get)>0:
     #
     #           return UserWarning(_('Success...'))
     #      else:
     #           return UserWarning(_('Oop Nothing...'))


          # return self.env[func_mod].myinfo('Downloading...', 'success')



     def info(self,info, type):
          return self.env[func_mod].myinfo(info, type)

     def action_reload(self):
          self.env[func_mod].reload()

     def action_close(self):
          self.env[func_mod].close_popup()

