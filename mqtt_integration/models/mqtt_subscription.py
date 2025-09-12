# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from ..utils import broker_client
from paho.mqtt.properties import Properties
from paho.mqtt.packettypes import PacketTypes
import json
import base64
import logging
import threading

_logger = logging.getLogger(__name__)


class MQTTSubscription(models.Model):
    _name = 'mqtt.subscription'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'MQTT Subscription'

    name = fields.Char(string="Name", compute="_compute_name", readonly=True)
    status = fields.Selection([
        ('new', 'New'),
        ('subscribe', 'Subscribed'),
        ('unsubscribe', 'Unsubscribed'),
        ('fail', 'Failed'),
    ], default='new', string='Status')
    direction = fields.Selection([
        ('outgoing', 'Outgoing'),
        ('incoming', 'Incoming')
    ], string='Direction', default='outgoing')
    format_payload = fields.Selection([
        ('plaintext', 'Plaintext'),
        ('json', 'JSON'),
        ('base64', 'Base64'),
        ('hex', 'Hex')
    ], default='plaintext', string='Format Payload',
        help='Format Payload to Publish\n'
             '• JSON: Must be valid JSON format\n'
             '• Base64: Must be valid Base64 encoding\n'
             '• Hex: Must be valid hexadecimal format\n'
             '• Plaintext: Any text format')
    broker_id = fields.Many2one('mqtt.broker', string='Broker', required=True)
    topic_id = fields.Many2one('mqtt.topic', string='Topic', domain="[('broker_id', '=', broker_id)]", required=True)
    metadata_id = fields.Many2one('mqtt.metadata', string='Metadata')
    is_metadata_domain = fields.Boolean(string='Domain Metadata by Topic', help="Metadata domain with topic", default=False)
    history_ids = fields.One2many('mqtt.message.history', 'subscription_id', string='Signal History')
    payload = fields.Text(string='Payload', required=True, help='Message payload. Format must match the selected Format Payload type.')
    qos = fields.Integer(string='QoS', default=0)
    retain = fields.Boolean(string='Retain', default=False,
                            help="- Used to mark messages for retention on the broker.\n"
                                 "- Want clients to subscribe later and also receive the latest status immediately.\n"
                                 "- Should be used for signals (e.g. relays, sensors, etc) to get the latest value of the topic.\n"
                                 "- Not for storing data history, logs, special events that are constantly.")
    subscription_time = fields.Datetime(string='Subscription Time')
    unsubscription_time = fields.Datetime(string='Unsubscription Time')
    progressing_subscription = fields.Char(string='Progressing Subscription', readonly=True)
    publish_at = fields.Datetime(string='Message Publish At')
    topic_count = fields.Integer(string="Topic Count", compute="_compute_topic_count")
    is_allow_user_property = fields.Boolean(
        string='Allow User Property',
        default=False,
        help="Enable to allow user properties in MQTT messages"
    )
    outgoing_message_count = fields.Integer(
        string="Outgoing Message Count",
        compute="_compute_message_count",
    )
    incoming_message_count = fields.Integer(
        string="Incoming Message Count",
        compute="_compute_message_count",
    )

    @api.constrains('format_payload', 'payload')
    def _check_payload_format(self):
        """Validate payload format based on format_payload selection"""
        for record in self:
            if not record.payload:
                continue

            if record.format_payload == 'json':
                try:
                    # Check for valid JSON
                    parsed_json = json.loads(record.payload)

                    # Check JSON is not completely empty
                    if parsed_json is None:
                        raise ValidationError("JSON payload cannot be null")

                except json.JSONDecodeError as e:
                    raise ValidationError(
                        f"Invalid JSON format in payload.\n"
                        f"Error: {e.msg} at line {e.lineno}, column {e.colno}"
                    )
                except Exception as e:
                    raise ValidationError(f"JSON validation error: {str(e)}")

            elif record.format_payload == 'base64':
                try:
                    # Validate Base64 format
                    base64.b64decode(record.payload, validate=True)
                except Exception:
                    raise ValidationError("Invalid Base64 format in payload")

            elif record.format_payload == 'hex':
                try:
                    # Validate Hex format
                    cleaned_hex = record.payload.replace(' ', '').replace('\n', '')
                    bytes.fromhex(cleaned_hex)
                except ValueError:
                    raise ValidationError("Invalid Hex format in payload")

    @api.onchange('is_metadata_domain', 'topic_id')
    def _onchange_metadata_domain(self):
        if all([self.is_metadata_domain, self.topic_id,
                self.metadata_id]) and self.metadata_id.topic_id != self.topic_id:
            self.metadata_id = False

    @api.depends('broker_id', 'topic_id')
    def _compute_name(self):
        for rec in self:
            if rec.broker_id and rec.topic_id:
                broker_name = rec.broker_id.name or "Unknown Broker"
                topic_name = rec.topic_id.name or "Unknown Topic"
                rec.name = f"{broker_name} - {topic_name}"
            else:
                rec.name = "Incomplete Configuration"

    @api.depends('history_ids.direction')
    def _compute_message_count(self):
        for rec in self:
            rec.outgoing_message_count = len([
                res for res in rec.history_ids if res.direction == 'outgoing'
            ])
            rec.incoming_message_count = len([
                res for res in rec.history_ids if res.direction == 'incoming'
            ])

    @api.depends('topic_id', 'broker_id')
    def _compute_topic_count(self):
        for rec in self:
            rec.topic_count = self.env['mqtt.topic'].search_count([
                ('id', '=', rec.topic_id.id),
                ('broker_id', '=', rec.broker_id.id)
            ])

    @api.constrains('format_payload', 'payload')
    def _check_json_payload(self):
        """Validate a payload format when format_payload is 'json'"""
        for record in self:
            if record.format_payload == 'json' and record.payload:
                try:
                    json.loads(record.payload)
                except (json.JSONDecodeError, ValueError) as e:
                    raise ValidationError(
                        f"Payload must be valid JSON format when Format Payload is 'JSON'. "
                        f"Error: {str(e)}"
                    )

    def action_format_json_payload(self):
        """Format JSON payload for better readability"""
        self.ensure_one()
        if self.format_payload == 'json' and self.payload:
            try:
                parsed = json.loads(self.payload)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.payload = formatted
            except json.JSONDecodeError:
                _logger.error(f"Cannot format invalid JSON payload.")
                raise UserError("Cannot format invalid JSON payload.")

    def action_validate_payload(self):
        """Manually validate a payload format"""
        self.ensure_one()
        try:
            self._check_payload_format()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Validation Success',
                    'message': f'{self.format_payload.upper()} payload is valid.',
                    'type': 'success',
                    'sticky': False,
                }
            }
        except ValidationError as e:
            _logger.error(f"Validation failed: {e}")
            raise UserError(f"Validation failed: {str(e)}")

    def action_publish_message(self):
        for rec in self:
            broker = rec.broker_id
            topic = rec.topic_id

            # Validate required fields
            if not broker:
                raise UserError('Broker not found!')
            if not topic and topic.status != 'confirm':
                raise UserError('Topic confirmed not found!')
            if broker.status != 'connect':
                raise UserError("Broker not connected!")
            if rec.status != 'subscribe':
                raise UserError("Subscription not active!")

            # Validate a payload format before publishing
            try:
                rec._check_payload_format()
            except ValidationError as e:
                _logger.error(f"PuPayload validation failed: {e}")
                raise UserError(f"Payload validation failed: {str(e)}")

            try:
                client = broker_client(
                    client_id=broker.client_id,
                    clean_session=broker.clean_session,
                    protocol=broker.protocol
                )
                if broker.username:
                    client.username_pw_set(broker.username, broker.password or None)
                client.connect(broker.host, int(broker.port), broker.keepalive)

                # Prepare payload based on format
                formatted_payload = rec._prepare_payload_for_publish()

                properties = Properties(PacketTypes.PUBLISH)
                if not rec.metadata_id:
                    client.publish(
                        topic=rec.topic_id.name,
                        payload=formatted_payload,
                        qos=rec.qos or 0,
                        retain=rec.retain or False,
                        properties=None,
                    )
                else:
                    properties.ContentType = rec.metadata_id.content_type or 'text/plain'
                    properties.PayloadFormatIndicator = 1 if rec.format_payload in ['json', 'plaintext'] else 0
                    properties.MessageExpiryInterval = int(rec.metadata_id.expiry) or 0
                    properties.ResponseTopic = rec.metadata_id.response_topic or 'unknown Response Topic'.encode()
                    corr = rec.metadata_id.correlation_data
                    if isinstance(corr, str) and corr != '':
                        properties.CorrelationData = corr.encode()
                    else:
                        properties.CorrelationData = corr if corr else 'unknown Correlation Data'.encode()
                    properties.SubscriptionIdentifier = int(rec.metadata_id.subscription_identifier) or 1
                    if rec.metadata_id.metadata_value_ids:
                        user_properties = [
                            (prop.key, prop.value) for prop in rec.metadata_id.metadata_value_ids
                        ]
                        if user_properties:
                            properties.UserProperty = user_properties
                    else:
                        properties.UserProperty = []

                    client.publish(
                        topic=rec.topic_id.name,
                        payload=formatted_payload,
                        qos=rec.qos or 0,
                        retain=rec.retain or False,
                        properties=properties,
                    )

                client.disconnect()

                # Data message for history
                data_message = {
                    'broker_id': rec.broker_id.id,
                    'metadata_id': rec.metadata_id.id if rec.metadata_id else False,
                    'subscription_id': rec.id,
                    'topic': rec.topic_id.name,
                    'format_payload': rec.format_payload,
                    'payload': rec.payload,
                    'qos': rec.qos,
                    'retain': rec.retain,
                    'direction': rec.direction,
                    'timestamp': fields.Datetime.now(),
                }

                # Record the time of sending
                rec.publish_at = fields.Datetime.now()

                # Save history
                self.env['mqtt.message.history'].create(data_message)

            except Exception as e:
                _logger.error(f"Publish message failed: {e}")
                raise UserError(f'Publish message failed: {str(e)}.')

    def _prepare_payload_for_publish(self):
        """Prepare payload based on format_payload setting"""
        if self.format_payload == 'json':
            # Ensure JSON is properly formatted
            try:
                parsed = json.loads(self.payload)
                return json.dumps(parsed, separators=(',', ':'))
            except json.JSONDecodeError:
                raise UserError("Invalid JSON payload.")

        elif self.format_payload == 'base64':
            try:
                return base64.b64decode(self.payload)
            except Exception:
                raise UserError("Invalid Base64 payload.")

        elif self.format_payload == 'hex':
            try:
                cleaned_hex = self.payload.replace(' ', '').replace('\n', '')
                return bytes.fromhex(cleaned_hex)
            except ValueError:
                raise UserError("Invalid Hex payload.")

        else:  # plaintext
            return self.payload

    def action_subscribe(self):
        """Subscribe to topic and update status."""
        for rec in self:
            broker = rec.broker_id
            topic = rec.topic_id
            if not broker:
                raise UserError("Broker not selected.")
            if not topic or topic.status != 'confirm':
                raise UserError('Topic confirmed not found!')

            try:
                userdata = {
                    'topic': rec.topic_id.name,
                    'qos': rec.qos,
                    'subscription_id': rec.id,
                    'broker_id': broker.id,
                    'dbname': self.env.cr.dbname,
                    'uid': self.env.uid,
                    'context': self.env.context,
                }
                client = broker_client(
                    client_id=broker.client_id,
                    clean_session=broker.clean_session,
                    protocol=broker.protocol,
                    userdata=userdata
                )
                if broker.username:
                    client.username_pw_set(broker.username, broker.password or None)

                client.connect(broker.host, int(broker.port), broker.keepalive)
                client.subscribe(rec.topic_id.name, qos=rec.qos or 0)
                threading.Event().wait(0.5)
                client.disconnect()

                rec.write({
                    'status': 'subscribe',
                    'progressing_subscription': 'Subscription successfully.',
                    'subscription_time': fields.Datetime.now()
                })

                self.env['bus.bus']._sendone(
                    userdata['dbname'],
                    ['mqtt_realtime'],
                    {
                        'topic': rec.topic_id.name,
                        'payload': rec.payload,
                        'qos': rec.qos,
                        'direction': 'outgoing',
                        'broker': rec.broker_id.name,
                        'timestamp': str(fields.Datetime.now())
                    }
                )

                _logger.info(f"Subscribed to {rec.topic_id.name} on broker {broker.name}.")

                self.env.cr.commit()
                # Restart the listener if running to apply immediately
                if broker.listener_status == 'run':
                    _logger.info(f"Restarting listener for broker {broker.name} after subscribe.")
                    broker.action_reconnect()

            except Exception as e:
                _logger.error(f"Subscribe to {rec.topic_id.name} error: {e}")
                rec.write({
                    'status': 'fail',
                    'progressing_subscription': f"Fail Subscribe to {rec.topic_id.name}.",
                })

    def action_unsubscribe(self):
        """Unsubscribe from topic and update status."""
        for rec in self:
            broker = rec.broker_id
            if not broker:
                raise UserError("Broker not selected.")

            try:
                client = broker_client(
                    client_id=broker.client_id,
                    clean_session=broker.clean_session,
                    protocol=broker.protocol
                )
                if broker.username:
                    client.username_pw_set(broker.username, broker.password or None)

                client.connect(broker.host, int(broker.port), broker.keepalive)
                client.unsubscribe(rec.topic_id.name)
                threading.Event().wait(0.5)
                client.disconnect()

                rec.write({
                    'status': 'unsubscribe',
                    'progressing_subscription': 'Unsubscribe successfully.',
                    'unsubscription_time': fields.Datetime.now(),
                })

                self.env['bus.bus']._sendone(
                    self.env.cr.dbname,
                    ['mqtt_realtime'],
                    {
                        'topic': rec.topic_id.name,
                        'payload': rec.payload,
                        'qos': rec.qos,
                        'direction': 'outgoing',
                        'broker': rec.broker_id.name,
                        'timestamp': str(fields.Datetime.now())
                    }
                )

                _logger.info(f"Unsubscribed from {rec.topic_id.name} on broker {broker.name}.")

                self.env.cr.commit()
                # Restart the listener if running to apply immediately
                if broker.listener_status == 'run':
                    _logger.info(f"Restarting listener for broker {broker.name} after unsubscribe.")
                    broker.action_stop_listener()
                    threading.Event().wait(0.5)
                    broker.action_start_listener()

            except Exception as e:
                _logger.error(f"Unsubscribe to {rec.topic_id.name} error: {e}")
                rec.write({
                    'status': 'fail',
                    'progressing_subscription': f"Failed to Unsubscribe to {rec.topic_id.name}.",
                })

    def action_renew_subscription(self):
        """Renew MQTT Subscription."""
        for broker in self:
            broker.write({
                'status': 'new',
                'subscription_time': False,
                'unsubscription_time': fields.Datetime.now(),
                'progressing_subscription': 'Renew MQTT Subscription successfully.',
            })

    def action_review_topic(self):
        self.ensure_one()
        if not self.topic_id or not self.broker_id:
            raise UserError("Missing topic or broker.")

        action = self.env.ref('mqtt_integration.action_mqtt_topic').read()[0]
        action.update({
            'domain': [
                ('id', '=', self.topic_id.id),
                ('broker_id', '=', self.broker_id.id)
            ],
            'context': {
                'default_id': self.topic_id.id,
                'default_broker_id': self.broker_id.id
            }
        })
        return action

    def action_review_incoming_history(self):
        self.ensure_one()
        action = self.env.ref('mqtt_integration.action_mqtt_incoming_message').read()[0]
        action.update({
            'domain': [
                ('subscription_id', '=', self.id),
                ('direction', '=', 'incoming'),
            ],
            'context': {
                'default_subscription_id': self.id,
                'default_direction': 'incoming'
            }
        })
        return action

    def action_review_outgoing_history(self):
        self.ensure_one()
        action = self.env.ref('mqtt_integration.action_mqtt_outgoing_message').read()[0]
        action.update({
            'domain': [
                ('subscription_id', '=', self.id),
                ('direction', '=', 'outgoing'),
            ],
            'context': {
                'default_subscription_id': self.id,
                'default_direction': 'outgoing'
            }
        })
        return action
