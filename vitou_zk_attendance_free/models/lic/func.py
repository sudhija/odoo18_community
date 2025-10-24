# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82

###############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


from datetime import datetime, timedelta, time
import pytz


class VitouSlotFunc(models.Model):
     _name = 'vitouzkf.func'
     _description = "Function"



     #report leading zero
     def leading_zero(self, value,digit):
          f ="{:0"+ digit +"d}"
          #print(f)
          # return "{:09d}".format(value)
          return f.format(value)
     def reload(self):
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
          }

     def myinfo(self, message, infotype):
          # /'success', 'info', 'warning'
          return {
               'type': 'ir.actions.client',
               'tag': 'display_notification',
               'params': {
                    'message': message,
                    'type': infotype,
                    'sticky': False
               }
          }

     def get_staff(self, user_id):
          data = self.env['hr.employee'].sudo().search([('user_id', '=', user_id)])
          staffname = ""
          if len(data) > 0:
               staffname = data.name
          return staffname

     def open_new_form(self, name, model, folder_formname):
          return {

               'name': name,  # 'Checkin',

               'view_mode': 'form',

               'res_model': model,  # 'room.booking',

               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form

               # 'context': {'default_name': self.name.id},
               #'domain':domain,
               'target': 'new',

               'type': 'ir.actions.act_window',

          }

     def open_action_view(self, name, model, view_mode, kanban_name, form_name,tree_name, graph_name,context={},domain=[], taget='current'):
          # v_id = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+form_name+"')}),(0, 0, {'view_mode': 'graph', 'view_id': ref('"+graph_name+"')})]"
          # v_id_kanban = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')})]"
          # v_id_kanban_form = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+form_name+"')})]"
          # v_id_kanban_tree = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+tree_name+"')})]"

          data =[]
          data.append("(5, 0, 0)")
          if tree_name !='':
               data.append("(5, 0, {'view_mode': 'list', 'view_id':  ref('" + tree_name + "')})")
          if form_name !='':
               data.append("(5, 0, {'view_mode': 'form', 'view_id':  ref('" + form_name + "')})")
          if kanban_name !='':
               data.append("(5, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')})")
          if graph_name !='':
               data.append("(5, 0, {'view_mode': 'graph', 'view_id':  ref('" + graph_name + "')})")

          return {

               'name': name,  # 'Checkin',
               'view_mode': view_mode, #'kanban,tree,form'
               'res_model': model,  # 'room.booking',
               'view_ids eval=': data,
               #'context': {'default_name': self.name.id},
               'context': context,
               'target': taget,
               'domain':domain,
               'type': 'ir.actions.act_window',

          }

     def open_action_view_all(self, name, model, view_mode, kanban_name, form_name,tree_name, graph_name,pivot_name,context={},domain=[], taget='current'):
          # v_id = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+form_name+"')}),(0, 0, {'view_mode': 'graph', 'view_id': ref('"+graph_name+"')})]"
          # v_id_kanban = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')})]"
          # v_id_kanban_form = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+form_name+"')})]"
          # v_id_kanban_tree = "[(5, 0, 0), (0, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')}), (0, 0, {'view_mode': 'form', 'view_id': ref('"+tree_name+"')})]"

          data =[]
          data.append("(5, 0, 0)")
          if tree_name != '':
               data.append("(5, 0, {'view_mode': 'list', 'view_id':  ref('" + tree_name + "')})")
          if form_name != '':
               data.append("(5, 0, {'view_mode': 'form', 'view_id':  ref('" + form_name + "')})")
          if kanban_name != '':
               data.append("(5, 0, {'view_mode': 'kanban', 'view_id':  ref('"+kanban_name+"')})")
          if graph_name != '':
               data.append("(5, 0, {'view_mode': 'graph', 'view_id':  ref('" + graph_name + "')})")
          if pivot_name != '':
               data.append("(5, 0, {'view_mode': 'pivot', 'view_id':  ref('" + pivot_name + "')})")

          return {

               'name': name,  # 'Checkin',
               'view_mode': view_mode, #'kanban,tree,form'
               'res_model': model,  # 'room.booking',
               'view_ids eval=': data,
               #'context': {'default_name': self.name.id},
               'context': context,
               'target': taget,
               'domain':domain,
               'type': 'ir.actions.act_window',

          }


     def open_new_form(self, name, model, folder_formname, view_mode='form',target='new', domain=[]):
          return {

               'name': name,  # 'Checkin',

               'view_mode': view_mode,

               'res_model': model,  # 'room.booking',

               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form

               # 'context': {'default_name': self.name.id},
               'domain': domain,
               'target': target,

               'type': 'ir.actions.act_window',

          }
     def open_new(self, name, model, folder_formname, view_mode='form',target='new'):
          return {

               'name': name,  # 'Checkin',

               'view_mode': view_mode,

               'res_model': model,  # 'room.booking',

               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form

               # 'context': {'default_name': self.name.id},

               'target': target,

               'type': 'ir.actions.act_window',

          }



     def open_form_by_id(self, title, model, folder_formname, id, target, view_mode='form'):
          # return self.env['vitouslot.func'].open_form_by_id( 'Clean Request', 'cleaning.request',
          # 'vitou_hotel_management.cleaning_request_view_form', room_clean.id, 'current')
          return {
               'name': title,  # 'Checkin',
               'view_mode': view_mode, #'form',
               'res_model': model,  # 'room.booking',
               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form
               'res_id': id,  # for get by id
               # 'res_id': ids.id,
               # 'context': {'default_cleaning_type': 'room', 'default_room_id': rec.id}, #for default value
               'target': target,  # 'new','current','inline','fullscreen'
               'type': 'ir.actions.act_window',

          }

     def open_form_with_default(self, title, model, folder_formname, context, target, view_mode='form'):
          # return self.env['vitouslot.func'].open_form_with_default( 'Clean Request', 'cleaning.request',
          # 'vitou_hotel_management.cleaning_request_view_form', {'default_cleaning_type': 'room', 'default_room_id': rec.id}, 'current' )

          return {
               'name': title,  # 'Checkin',
               'view_mode': view_mode,#'form',
               'res_model': model,  # 'room.booking',
               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form
               # 'res_id': id,  # for get by id
               # 'res_id': ids.id,
               'context': context,
               # 'context': {'default_cleaning_type': 'room', 'default_room_id': rec.id}, #for default value
               'target': target,  # 'new','current','inline','fullscreen'
               'type': 'ir.actions.act_window',

          }

     def open_view_with_default(self, title, model, folder_formname, folder_formname1,  context, target, view_mode='form'):
          # return self.env['vitouslot.func'].open_form_with_default( 'Clean Request', 'cleaning.request',
          # 'vitou_hotel_management.cleaning_request_view_form', {'default_cleaning_type': 'room', 'default_room_id': rec.id}, 'current' )

          # 'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
          return {
               'name': title,  # 'Checkin',
               'view_mode': view_mode,#'form',
               'res_model': model,  # 'room.booking',
               'view_id': self.env.ref(folder_formname).id,  # vitou_hotel_management.room_booking_view_form
               'views': [(self.env.ref(folder_formname).id, 'list'), (self.env.ref(folder_formname1).id, 'form')],
               # 'res_id': id,  # for get by id
               # 'res_id': ids.id,
               'context': context,
               # 'context': {'default_cleaning_type': 'room', 'default_room_id': rec.id}, #for default value
               'target': target,  # 'new','current','inline','fullscreen'
               'type': 'ir.actions.act_window',
               #'domain': domain,

          }

     # def open_action_window(self):
     #      return {
     #           'type': 'ir.actions.act_window',
     #           'res_model': 'ir.attachment',
     #           'view_mode': 'kanban,tree,form',
     #            'target': 'new',
     #            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
     #      }





     def open_report_all(self, modulename_reportactionid, reportname):
          return {
               'type': 'ir.actions.report',
               'report_type': 'qweb-pdf',
               'report_name': modulename_reportactionid,
               'report_file': modulename_reportactionid,
               'name': reportname,
          }


     def open_report(self, modulename_reportactionid):
          #self.ensure_one()
          #self.sent = True
          #modulename_reportactionid='vitou_slot_system.it_request_profile_report_template_slot_payout_slip'
          report_action = self.env.ref(modulename_reportactionid)
          # < record id = "it_request_profile_report_template_slot_payout_slip" model = "ir.actions.report" >
          return report_action.report_action(self)

     def open_report_with_record(self, docids, modulename_reportactionid):
          # get the report action back as we will need its data
          # report = self.env['ir.actions.report']._get_report_from_name(module_reportname)
          # get the records selected for this rendering of the report

          # ids = self.get_ids(operationday_id)
          #return self.env['vitouslot.func'].open_report_with_record(ids,'vitou_slot_system.report_template_vitouslot_winloss_report_detail')

          report = self.env.ref(modulename_reportactionid)
          obj = self.env[report.model].browse(docids)
          #print('==>', obj)

          return report.report_action(obj)

     def get_ids(self, model_name, domain=[]):
          #  ids = self.env['vitouslot.func'].get_ids('vitouslot.collection',[('operationday_id','=',operationday_id)])
          ids_search = self.env[model_name].sudo().search(domain)
          ids = [record.id for record in ids_search]
          # print(ids)
          return ids



     def get_field_name(self, search_list):
          # print(self.env['vitouslot.func'].get_field_name(room))
          return print(search_list._fields)



     def debug(self):
          #notworking, must direct use
          import pdb
          pdb.set_trace()




     def close_popup(self):
          return {
               'type': 'ir.actions.client',
               'tag': 'reload',
          }
          #return {'type': 'ir.actions.act_window_close'}

     def combo_user(self):
          user_get = self.env['res.users'].sudo().search([])
          str = []
          for u in user_get:
               str.append((u.id, u.name))

          #print(str)
          return str
     def combo_add(self, model, domain, isName):
          gets = self.env[model].sudo().search(domain)
          str = []
          for u in gets:
               if isName==True:
                    str.append((u.id, u.name))
               else:
                    str.append((u.id, u.id))

          #print(str)
          return str
     def get_name_from_id(self, model, field_id, id_value):
          gets = self.env[model].sudo().search([(field_id,'==',id_value)])
          return gets.name
     def get_id_from_name(self, model, field_name, name_value):
          gets = self.env[model].sudo().search([(field_name,'==',name_value)])
          return gets.id

     def date_to_ymd(self, date):
          return date.strftime('%Y-%m-%d')

     def get_user_name_from_id(self, user_id):
          user_name = self.env['res.users'].sudo().search([('id','=',user_id)]).name
          return user_name



     def MinValue(self, check_in_hh_mm, hr_base_from_base_in1, hr_base_from_base_in2, hr_base_from_base_out1,
                  hr_base_from_base_out2):
          # i =0
          v1 = hr_base_from_base_in1
          v2 = hr_base_from_base_in2
          v3 = hr_base_from_base_out1
          v4 = hr_base_from_base_out2

          data = []

          data.append({'name': 'hr_base_from_base_in1', 'hm': v1, 'in_out': 'in1'})
          data.append({'name': 'hr_base_from_base_in2', 'hm': v2, 'in_out': 'in2'})
          data.append({'name': 'hr_base_from_base_out1', 'hm': v3, 'in_out': 'out1'})
          data.append({'name': 'hr_base_from_base_out2', 'hm': v4, 'in_out': 'out2'})

          # print(data)

          idx = self.getnearval(data, check_in_hh_mm)
          return idx

     def getnearval(self, L, target):
          # result = vals.get('order_line')
          # desired_id = result[0][2]["tax_id"][0][2][0]
          # print(L)
          lst = [];

          for d in L:
               lst.append(d["hm"])

          idx = min(lst, key=lambda x: abs(x-target))

          res = None
          for sub in L:
               if sub['hm'] == idx:
                    res = sub
                    break

          # print(target,'=', idx,'=', res["in_out"])
          return res["in_out"]

     def val1_small(self, val1, val2):
          if val1 < val2:
               return True
          else:
               return False

     def convertDate_to_utc(self, check_in):
          # atten_time = check_in.timestamp
          local_tz = pytz.timezone(self.env.user.partner_id.tz or 'GMT')
          local_dt = local_tz.localize(check_in, is_dst=None)
          utc_dt = local_dt.astimezone(pytz.utc)
          attendance_time = utc_dt.strftime("%Y-%m-%d %H:%M:%S")
          atten_time_datetime = datetime.strptime(attendance_time, "%Y-%m-%d %H:%M:%S")
          atten_date = atten_time_datetime.date()

          return atten_date

     def convert_date_to_local(self, date_convert):
          user_tz = self.env.user.tz or pytz.utc
          local = pytz.timezone(user_tz)
          format_data = "%Y-%m-%d %H:%M:%S"
          # DEFAULT_SERVER_DATETIME_FORMAT

          display_date_result = datetime.strftime(
               pytz.utc.localize(datetime.strptime(str(date_convert), format_data)).astimezone(local), format_data)
          # atten_date = display_date_result.date()
          return display_date_result

     def convert_date_to_hhmm(self, date_convert):
          # hhmm = date_convert.strftime('%H:%M')
          # print(date_convert)
          dateteme = self.convert_str_to_datetime(date_convert)

          hh = dateteme.strftime('%H')
          mm = dateteme.strftime('%M')
          hh_int = int(hh)
          mm_int = float(mm) / 100
          hh_mm_int = hh_int + mm_int
          return hh_mm_int

     def convert_str_to_datetime(self, date_str):

          # input = "2018-10-09 20.00"
          d = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")  # parse to datetime object
          return d
     def convert_h_dot_m_to_int(self, h_do_m):
          #h_do_m = 3.14
          h_m_round = round(h_do_m, 2)
          h_str, m_str = h_m_round.split('.')
          integer = int(h_str)  # 3
          fraction = int(m_str)  # 14
          mm_int = self.convert_to_minute_int(fraction)
          r = str(integer) + ':' + str(mm_int)
          return r


     def convert_to_minute_int(self, mm):
          mm_int = mm/60
          return int(mm_int)

     def close_popup(self):
          # do any server-side logic here…
          return {'type': 'ir.actions.act_window_close'}

     def get_name_from_id(self, moduleName, fieldName, id):
          r = self.env[moduleName].sudo().search([(fieldName,'=', id)])
          return r.name

     def get_departmentname(self, employee_name):
          r = self.env['hr.employee'].sudo().search([('name','=', employee_name)])
          if r:
               return r.department_id.name
          else:
               return None

     def chunker(self, seq, size):
          for pos in range(0, len(seq), size):
               yield seq[pos:pos + size]
          # Usage
          # for pair in chunker(data, 2):
          #      print(pair)






