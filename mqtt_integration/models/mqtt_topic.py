# -*- coding: utf-8 -*-
from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class MQTTTopic(models.Model):
    _name = 'mqtt.topic'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'MQTT Topics'

    name = fields.Char(string='Name', help="The name of the MQTT topic, e.g., 'home/temperature'.")
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed')
    ], default='draft', string='Status')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, required=True)
    broker_id = fields.Many2one('mqtt.broker', string='Broker', required=True)
    description = fields.Text(string='Description')
    qos = fields.Integer(string='QoS', default=0)
    subscription_identifier = fields.Integer(string='Subscription Identifier')
    no_local_flag = fields.Boolean(string='No Local Flag', default=False)
    retain_as_published_flag = fields.Boolean(string='Retain as Published Flag', default=False)
    retain_handling = fields.Integer(string='Retain handling', default=0)
    last_confirmed = fields.Datetime(string="Last Confirmed")

    def action_set_to_draft(self):
        for rec in self:
            rec.write({'status': 'draft'})

    def action_confirm(self):
        for rec in self:
            rec.write({
                'status': 'confirm',
                'last_confirmed': fields.Datetime.now(),
            })