# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MQTTMetadata(models.Model):
    _name = 'mqtt.metadata'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'MQTT Metadata (User Properties)'
    _order = "timestamp desc"

    name = fields.Char(string='Name', help="The name of the MQTT metadata, e.g.")
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, readonly=True)
    direction = fields.Selection(
        [('outgoing', 'Outgoing'), ('incoming', 'Incoming')],
        default='outgoing', string='Direction', required=True
    )
    topic_id = fields.Many2one('mqtt.topic', string='Topic')
    history_id = fields.Many2one('mqtt.message.history', string='History')
    subscription_id = fields.Many2one('mqtt.subscription', string='Subscription')
    metadata_value_ids = fields.One2many(
        'mqtt.metadata.value', 'metadata_id', string='Metadata Values'
    )
    content_type = fields.Selection(
        [('application/json', 'JSON'), ('text/plain', 'Plain Text'), ('image/jpeg', 'JPEG Image')],
        default='text/plain',
        string='Content Type',
        help="Defines the content type of the payload, "
             "e.g. application/json, text/plain, image/jpeg, etc.\n"
             "Uses:\n"
             "Helps the receiver determine what type of payload "
             "to process (e.g. if the receiver is json, parse json).\n"
             "Useful when you transmit diverse data."
    )
    format_payload = fields.Selection(
        [('0', '0 - Binary String'), ('1', '1 - Text String')],
        default='1',
        string='Payload Format Indicator',
        help="Select payload type: 0 (binary string) or 1 (text string).\n"
             "Uses:\n"
             "Determines the data type of the payload, serving correct processing at the receiver."
    )
    expiry = fields.Integer(
        default=30,
        string= 'Message Expiry Interval (seconds)',
        help="Set the message time to live (seconds). "
             "After this time, the message will be discarded by the broker "
             "if it has not been delivered to the subscriber.\n"
             "Uses:\n"
             "Ensures that the message does not exist forever if the subscriber connects too late."
    )
    response_topic = fields.Char(
        string='Response Topic',
        help="Defines the topic on which the receiver should publish a response message.\n"
             "Uses:\n"
             "Useful in systems that require “request-response” over MQTT, e.g. "
             "controlling a relay and receiving status feedback."
    )
    correlation_data = fields.Char(
        string='Correlation Data',
        help="Data included to correlate (link) between request and response (usually used with response topic).\n"
             "Uses:\n"
             "Serves scenarios for comparing and authenticating requests - responses."
    )
    subscription_identifier = fields.Integer(
        default=0,
        string='Subscription Identifier',
        help="Assigns an identifier to a subscription to distinguish different subscription streams.\n"
             "Uses:\n"
             "Easy to track subscription streams when analyzing/monitoring."
    )
