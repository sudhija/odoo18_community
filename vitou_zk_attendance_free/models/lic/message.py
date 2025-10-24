# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class VitouSlotType(models.Model):
     _name = 'vitouzkf.message'
     _description = "Message"

     title = fields.Char(required=True)
     message = fields.Text(required=True)
     type = fields.Selection(
          selection=[
               ('success', 'success'),
               ('error','error'),
               ('warning','warning'),
          ],
          default='success', string='Type'
     )

     # def action_close(self):
     #      return {
     #           'type': 'ir.actions.client',
     #           'tag': 'display_notification'
     #      }
     def action_ok(self):
          return {
               'type': 'ir.actions.client',
               'tag': 'reload'
          }

     def mymessage(self, title, type, message):

          data = self.env['vitouzkf.message'].sudo().search([])
          if len(data)>0:
               #update
               data.write( {'title': title, 'type':type , 'message': message})
               return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'vitouzkf.message',
                    'res_id': data.id,
                    'target': 'new'
               }
          else :
               #create
               data.create(
                    {'title': title, 'type':type , 'message': message})
               return {
                    'name': 'Message',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'vitouzkf.message',
                    'res_id': data.id,
                    'target': 'new'
               }

