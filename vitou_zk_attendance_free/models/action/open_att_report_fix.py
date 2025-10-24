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
from ..lic.globals import func_mod
from datetime import datetime, timedelta, time
from collections import defaultdict
import pytz

import numpy as np

try:
    from zk import ZK, const
except ImportError as e:
    raise ValidationError(_(e.message))


class VitouzkDownloadAtt(models.TransientModel):
    _name = 'vitouzkf.open.report.fix'
    _description = 'Open Attendance Monthly Fix'
    # _inherit = ['mail.thread']
    # _rec_name = "provider"
    # _sql_constraints = [
    #      ('name_unique', 'unique(name)', "Currency Code is duplicated!"),
    # ]

    date = fields.Date(string="Date in Month", default=fields.Date.today())
    department_id = fields.Many2one(comodel_name='hr.department', string='Department')

    # date_to = fields.Date(string="Date To", default=fields.Date.today())

    def action_open_report(self):
        self.env[func_mod].is_my_saft()
        """Button action for creating Sale Order Pdf Report"""
        data_get = self.get_data()
        data = {
            'data': data_get
        }
        # data = {
        #     'data_att': data_gen,
        #     'month': month
        # }
        # return ''
        # print(',=', data_get)

        if len(data_get)>0:
            return self.env.ref(
                'vitou_zk_attendance_free.report_template_vitouzkf_att_fix_report').report_action(self, data=data)
        else:
            return self.info('Nothing to generate report', 'warning')

    def get_data(self):
        # print('donwload...')
        att_mod = self.env['vitouzkf.attendance.all']
        hr_mod = self.env['hr.attendance']


        for rec in self:
            data = []
            dep_name_array = []
            date = rec.date
            # date_to = rec.date_to
            month = date.strftime('%Y-%m')

            if rec.department_id:
                domain_dep = ('department_id', '=', rec.department_id.id)
                domain = [('state', 'in', ['posted', 'done']), ('is_att', '=', True),
                          ('date_inout', 'ilike', month + '-%'),
                          domain_dep]
            else:
                domain = [('state', 'in', ['posted', 'done']), ('is_att', '=', True),
                          ('date_inout', 'ilike', month + '-%')]



            # print(domain)

            att_get = att_mod.sudo().search(domain, order='employee_id asc')

            if not att_get:
                raise ValidationError('No data for these selections!')
                    # self.info('No data for this month', 'warning'))

            emp_name = att_mod.read_group(
                domain=domain,
                fields=['employee_name','total_work_hour:sum'],
                groupby=['employee_name'],
                # order='employee_name asc'
            )

            dep_group = att_mod.read_group(
                domain=domain,
                fields=['department_id'],
                groupby=['department_id'],
            )

            for d in dep_group:
                dep_id = d["department_id"]
                dep_name =  d["department_id"][1]
                dep_name_array.append({'dep_name': dep_name})



            # print('dg=', dep_name_array)

            # print('en==', emp_name)
            # emp_name_new = [{'employee_name': x['employee_name'],'total_work_hour':x['total_work_hour']} for x in emp_name]

            data_new = []
            for emp_n in emp_name:
                emp_name_get = emp_n['employee_name']
                emp_dept = self.env[func_mod].get_departmentname(emp_name_get)

                if rec.department_id:
                    domain_dep = ('department_id', '=', rec.department_id.id)
                    # for emp in emp_name_new:
                    domain_g = [('state', 'in', ['posted', 'done']), ('is_att', '=', True), ('date_inout', 'ilike', month + '-%'),('employee_name','=', emp_name_get),domain_dep]
                else:
                    domain_g = [('state', 'in', ['posted', 'done']), ('is_att', '=', True),
                                ('date_inout', 'ilike', month + '-%'), ('employee_name', '=', emp_name_get)]

                att_groupby = att_mod.read_group(
                    domain=domain_g,
                    fields=['day','total_work_hour:sum'],
                    groupby=['day'],
                    orderby='day asc'
                )
                att_day_hour =[
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},

                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},

                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},
                    {'day': None, 'hour': 0},

                    {'day': None, 'hour': 0},
                ]
                # print('a==', att_day_hour)

                for att in att_groupby:
                    # print('==', att)
                    day = att['day']
                    hour = att['total_work_hour']
                    indx = int(day)-1
                    att_day_hour[indx:indx] = [{
                        'day': day,
                        'hour': round(hour, 1)
                    }]


                data_new.append({
                    'employee_name': emp_name_get,
                    'dep_name': emp_dept,
                    'total_work_hour': round(emp_n['total_work_hour'], 1),
                    'day_hour': att_day_hour

                })

        data.append({
                'month': month,
                'dep_name':dep_name_array,
                'data': data_new

        })

        # print('xx=', data)

        return data

    def info(self, info, type):
        return self.env[func_mod].myinfo(info, type)

    def action_reload(self):
        self.env[func_mod].reload()

    def action_close(self):
        self.env[func_mod].close_popup()





