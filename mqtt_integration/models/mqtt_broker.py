# -*- coding: utf-8 -*-
from odoo.modules.registry import Registry
from odoo import models, fields, api, SUPERUSER_ID
from odoo.exceptions import UserError
from ..utils import broker_client, get_first_or_zero
import os
import time
import math
import random
import string
import psutil
import logging
import platform
import threading

_logger = logging.getLogger(__name__)
broker_threads = {}
broker_stop_flags = {}


class MQTTBroker(models.Model):
    _name = 'mqtt.broker'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'MQTT Broker'

    name = fields.Char(string='Broker Name', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('disconnect', 'Disconnected'),
        ('connect', 'Connected'),
        ('error', 'Error'),
    ], default='draft', readonly=True)
    listener_status = fields.Selection([
        ('new', 'New'),
        ('stop', 'Stopped'),
        ('run', 'Running')
    ], default='new', readonly=True)
    url_scheme = fields.Selection([
        ('mqtt://', 'MQTT'),
        ('ws://', 'WS')], default='mqtt://', string='URI scheme', required=True, tracking=True)
    host = fields.Char(string='Host', default='broker.emqx.io', required=True, tracking=True)
    port = fields.Char(string='Port', default='1883', required=True, tracking=True)
    client_id = fields.Char(string='Client ID', copy=False, default=lambda self: self._random_client_id(), required=True)
    protocol = fields.Selection([
        ('MQTTv31', 'MQTTv31'),
        ('MQTTv311', 'MQTTv311'),
        ('MQTTv5', 'MQTTv5')], string='Protocol', default='MQTTv5', tracking=True, required=True)
    username = fields.Char(string='Username', default='', tracking=True)
    password = fields.Char(string='Password', default='')
    keepalive = fields.Integer(string='Keepalive (s)', default=60)
    auto_reconnect = fields.Boolean(string='Auto Reconnect', default=False)
    clean_session = fields.Boolean(string='Clean Session', default=False)
    note = fields.Text(string='Note')
    progressing_broker = fields.Char(string='Progressing Broker', readonly=True)
    broker_count = fields.Integer(string="Broker Count", compute="_compute_broker_count")
    host_info = fields.Char(string='Host Info', compute='_compute_host_info', readonly=True)
    last_connected = fields.Datetime(string="Last Connected")
    last_started = fields.Datetime(string="Last Started")

    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'Configuration brokers name must be unique!'),
        ('client_id_uniq', 'unique(client_id)', 'Client ID must be unique!'),
    ]

    def _compute_host_info(self):
        """Display information about the host running the service"""
        for record in self:
            system = platform.system()
            release = platform.release()
            process = psutil.Process(os.getpid())
            record.host_info = f"{system} {release}, PID: {process.pid}, Python: {platform.python_version()}"

    def _compute_broker_count(self):
        for rec in self:
            subscriptions = self.env['mqtt.subscription'].search([
                ('broker_id', '=', rec.id)
            ])
            rec.broker_count = len(subscriptions)

    @api.model
    def _random_client_id(self):
        return 'client_' + ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))

    def _get_connected_client(self, start_loop=False):
        """Utility: return a connected MQTT client for this broker."""
        self.ensure_one()
        from ..utils import broker_client
        client = broker_client(
            client_id=self.client_id,
            clean_session=self.clean_session,
            protocol=self.protocol
        )

        if self.username:
            client.username_pw_set(self.username, self.password or None)

        try:
            client.connect(self.host, int(self.port), self.keepalive)
        except Exception as e:
            _logger.error(f"Cannot connect to broker {self.name}: {e}")
            raise UserError(f"Cannot connect to broker {self.name}.")

        if start_loop:
            client.loop_start()
        return client

    def action_renew_broker(self):
        """Renew MQTT Broker"""
        for broker in self:
            try:
                client = broker._get_connected_client()
                if broker.status == 'draft' and client:
                    _logger.error(f"The broker {broker.name} not in draft status.")
                    raise UserError(f"The broker {broker.name} not in draft status.")

                subs = self.env['mqtt.subscription'].search([
                    ('broker_id', '=', broker.id),
                    ('status', '=', 'subscribe')
                ])
                for sub in subs:
                    sub.action_unsubscribe()

                client.disconnect()
                broker.action_stop_listener()
                broker.write({
                    'status': 'draft',
                    'listener_status': 'new',
                    'progressing_broker': 'Renew MQTT Broker successfully.',
                })
                _logger.info(f"MQTT Broker {broker.name} renew successfully.")

            except Exception as e:
                _logger.error(f"Error renew for broker {self.name}: {e}")
                broker.write({
                    'status': 'error',
                    'progressing_broker': f"Error renew for broker {self.name}.",
                })

    def action_connection(self):
        """Connection to the broker."""
        for broker in self:
            try:
                client = broker._get_connected_client()
                if broker.status == 'connect' and client:
                    _logger.error(f"Broker {broker.name} already connection.")
                    raise UserError(f"Broker {broker.name} already connection.")

                client.disconnect()
                broker.write({
                    'status': 'connect',
                    'progressing_broker': 'Connected successfully.',
                    'last_connected': fields.Datetime.now(),
                })
                _logger.info(f"MQTT Broker {broker.name} connected successfully.")

            except Exception as e:
                _logger.error(f"Error connect for broker {self.name}: {e}")
                broker.write({
                    'status': 'error',
                    'progressing_broker': f"Error connect for broker {self.name}.",
                })

    def action_disconnect(self):
        """Disconnect from the broker if connected."""
        for broker in self:
            try:
                client = broker._get_connected_client()
                if broker.status == 'disconnect' and client:
                    _logger.error(f"Broker {broker.name} already disconnected.")
                    raise UserError(f"Broker {broker.name} already disconnected.")
                if broker.status != 'connect' and client:
                    _logger.error(f"The broker {broker.name} must be in a connected state.")
                    raise UserError(f"The broker {broker.name} must be in a connected state.")

                client.disconnect()
                broker.action_stop_listener()
                broker.write({
                    'status': 'disconnect',
                    'progressing_broker': 'Disconnected successfully.',
                })
                _logger.info(f"MQTT Broker {broker.name} disconnect successfully.")

            except Exception as e:
                _logger.error(f"Error disconnect for broker {self.name}: {e}")
                broker.write({
                    'status': 'error',
                    'progressing_broker': f"Error disconnect for broker {self.name}.",
                })

    def action_reconnect(self):
        for broker in self:
            try:
                broker.action_disconnect()
                broker.action_stop_listener()
                time.sleep(1)
                broker.action_connection()
                broker.action_start_listener()
                _logger.info(f"Reconnect for broker {broker.name} successfully.")

            except Exception as e:
                _logger.error(f"Error reconnect for broker {broker.name}: {e}")
                broker.write({
                    'status': 'error',
                    'progressing_broker': f"Error reconnect for broker {self.name}.",
                })

    def action_start_listener(self):
        for broker in self:
            try:
                if broker.status != 'connect':
                    _logger.error(f"The broker {broker.name} must be in a connected state.")
                    raise UserError(f"The broker {broker.name} must be in a connected state.")
                if broker.listener_status == 'run' and broker.id in broker_threads and broker_threads[broker.id].is_alive():
                    _logger.error(f"Listener for broker {broker.name} already running.")
                    raise UserError(f"Listener for broker {broker.name} already running.")

                stop_event = threading.Event()
                broker_stop_flags[broker.id] = stop_event

                thread = threading.Thread(
                    target=broker._run_listener_thread_safe,
                    args=(broker.id, broker.env.cr.dbname, stop_event),
                    daemon=True
                )
                broker_threads[broker.id] = thread
                thread.start()

                broker.write({
                    'listener_status': 'run',
                    'progressing_broker': f"Listener for broker {broker.name} started successfully.",
                    'last_started': fields.Datetime.now()
                })
                _logger.info(f"Started listener for broker {broker.name}.")

            except Exception as e:
                _logger.error(f"Error start listener for broker {broker.name}: {e}")
                broker.write({
                    'status': 'error',
                    'progressing_broker': f"Error start listener for broker {self.name}.",
                })

    def action_stop_listener(self):
        for broker in self:
            try:
                if broker.listener_status != 'run':
                    _logger.warning(
                        f"Listener for broker {broker.name} is not running (current status: {broker.listener_status}).")
                    broker.write({'listener_status': 'stop'})
                    return

                stop_event = broker_stop_flags.get(broker.id)
                thread = broker_threads.get(broker.id)

                if stop_event:
                    stop_event.set()
                    _logger.info(f"Stop signal sent to listener for broker {broker.name}.")
                    if thread and thread.is_alive():
                        _logger.info(f"Waiting for listener thread of broker {broker.name} to stop...")
                        thread.join(timeout=5)
                        if thread.is_alive():
                            _logger.warning(f"Listener thread for broker {broker.name} did not stop after timeout.")
                    broker_stop_flags.pop(broker.id, None)
                    broker_threads.pop(broker.id, None)
                    broker.write({
                        'listener_status': 'stop',
                        'progressing_broker': f"Listener for broker {broker.name} stopped successfully.",
                    })
                    _logger.info(f"Fully disconnected broker {broker.name}.")
                else:
                    _logger.warning(
                        f"No active stop flag for broker {broker.name}. Maybe already stopped or Odoo has been restarted.")
                    broker.write({
                        'listener_status': 'stop',
                        'progressing_broker': f"Listener for broker {broker.name} already stopped or Odoo has been restarted.",
                    })

            except Exception as e:
                _logger.error(f"Error during broker {broker.name} shutdown: {e}")
                raise UserError(f"Error during broker {broker.name} shutdown.")

    @staticmethod
    def get_subscribed_topics_for_broker(env, broker_id):
        """Get a list of topic names subscribed to a broker"""
        subs = env['mqtt.subscription'].search([
            ('broker_id', '=', broker_id),
            ('status', '=', 'subscribe')
        ])
        subs = subs.with_context(prefetch_fields=['topic_id'])
        result = []
        for sub in subs:
            try:
                if sub.topic_id:
                    result.append(sub.topic_id.name)
            except Exception as e:
                continue

        return result

    def _run_listener_thread_safe(self, broker_id, dbname, stop_event):
        reg = Registry(dbname)
        with reg.cursor() as cr:
            env = api.Environment(cr, SUPERUSER_ID, {})
            broker = env['mqtt.broker'].browse(broker_id)
            topic_names = self.get_subscribed_topics_for_broker(env, broker.id)

            broker_data = {
                'id': broker.id,
                'name': broker.name,
                'host': broker.host,
                'port': broker.port,
                'keepalive': broker.keepalive,
                'username': broker.username,
                'password': broker.password,
                'client_id': broker.client_id,
                'protocol': broker.protocol,
                'clean_session': broker.clean_session,
            }

        client = broker_client(
            client_id=broker_data['client_id'],
            clean_session=broker_data['clean_session'],
            protocol=broker_data['protocol'],
        )
        if broker_data['username']:
            client.username_pw_set(broker_data['username'], broker_data['password'] or None)

        def on_connect(client, userdata, flags, rc, properties=None):
            if getattr(client, '_subscribed', False):
                return
            _logger.info(f"[{dbname}] Connected to broker {broker_data['name']}.")

            if topic_names:
                for topic in topic_names:
                    client.subscribe(topic)
                    _logger.info(f"[{broker_data['name']}] Batch subscribed to topic: {topic}")

            client._subscribed = True

        def on_message(client, userdata, msg):
            _logger.info(f"Message received on {msg.topic}: {msg.payload}")
            with Registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                topic_env = env['mqtt.topic']
                metadata_model = env['mqtt.metadata']
                metadata_value_model = env['mqtt.metadata.value']
                history_env = env['mqtt.message.history']

                topic = topic_env.search([('name', '=', msg.topic)], limit=1) or False
                sub_exist = env['mqtt.subscription'].search([
                    ('topic_id', '=', topic.id if topic else False),('status', '=', 'subscribe')
                ], limit=1)
                if not sub_exist:
                    _logger.warning(f"Topic {msg.topic} is not subscribed.")
                    return

                try:
                    # Process message properties and metadata
                    metadata = None
                    metadata_value = []

                    if hasattr(msg.properties, 'UserProperty'):
                        user_props = msg.properties.UserProperty or {}
                        _logger.info(f"UserProperty received on {msg.topic}: {msg.properties}")

                        # Properties MQTT
                        content_type = getattr(msg.properties, 'ContentType', None)
                        format_payload = getattr(msg.properties, 'PayloadFormatIndicator', None)
                        expiry = getattr(msg.properties, 'MessageExpiryInterval', None)
                        response_topic = getattr(msg.properties, 'ResponseTopic', None)
                        correlation_data = getattr(msg.properties, 'CorrelationData', None)
                        subscription_identifier = getattr(msg.properties, 'SubscriptionIdentifier', None)
                        metadata_data = {
                            'name': 'Metadata for ' + msg.topic + str(fields.Datetime.now()),
                            'topic_id': topic.id if topic else False,
                            'history_id': False,
                            'subscription_id': sub_exist.id if sub_exist else False,
                            'direction': 'incoming',
                            'content_type': content_type,
                            'format_payload': '1' if format_payload == 1 else '0',
                            'expiry': expiry,
                            'response_topic': response_topic,
                            'correlation_data': correlation_data,
                            'subscription_identifier': get_first_or_zero(subscription_identifier),
                            'metadata_value_ids': metadata_value,
                        }
                        metadata = metadata_model.create(metadata_data)
                        _logger.info(f"Metadata received on {msg.topic} created: {metadata.name or ''}.")

                        for key, value in user_props:
                            metadata_value_data = {
                                'key': key,
                                'value': value,
                                'timestamp': fields.Datetime.now(),
                                'metadata_id': metadata.id if metadata else False,
                                'topic_id': topic.id if topic else False,
                            }
                            metadata_value.append(metadata_value_model.create(metadata_value_data))

                    message_data = {
                        'broker_id': broker_id,
                        'metadata_id': metadata.id if metadata else False,
                        'subscription_id': sub_exist.id if sub_exist else False,
                        'topic': topic.name if topic else msg.topic,
                        'payload': msg.payload.decode(errors='ignore'),
                        'direction': 'incoming',
                        'qos': msg.qos,
                        'retain': msg.retain,
                        'timestamp': fields.Datetime.now(),
                    }
                    history = history_env.create(message_data)
                    _logger.info(f"Message history created for topic {msg.topic}: {history.name or ''}.")

                    # Update metadata with history and values
                    if metadata:
                        metadata.update({
                            'history_id': history.id if history else False,
                            'metadata_value_ids': [(6, 0, [mv.id for mv in metadata_value])] if metadata_value else False
                        })
                    _logger.info(f"Metadata updated with history and values for topic {msg.topic}.")

                except Exception as e:
                    _logger.error(f"Error processing message for topic {msg.topic}: {e}")

                # Save to bus for real-time updates
                env['bus.bus']._sendone(
                    dbname,
                    ['mqtt_realtime'],
                    {
                        'topic': msg.topic,
                        'payload': msg.payload.decode(errors='ignore'),
                        'broker': broker_data['name'],
                        'timestamp': str(fields.Datetime.now())
                    }
                )

                _logger.info(f"Saved MQTT messages to database: {topic.broker_id.name if topic else 'Unknow'} - {msg.topic}.")
                cr.commit()

        def on_disconnect(client, userdata, rc, properties=None, reason_codes=None):
            reason_str = getattr(rc, 'name', str(rc))
            _logger.warning(f"[{dbname}] Disconnected from {broker_data['name']} - Reason: {reason_str}.")

        client.on_connect = on_connect
        client.on_message = on_message
        client.on_disconnect = on_disconnect

        try:
            client.connect(broker_data['host'], int(broker_data['port']), broker_data['keepalive'])
            client.loop_start()
            _logger.info(f"[{dbname}] Initial connection for {broker_data['name']} successfully.")

        except Exception as e:
            _logger.error(f"[{dbname}] Initial connection failed for {broker_data['name']}: {e}")
            raise UserError(f"[{dbname}] Initial connection failed for {broker_data['name']}.")

        # === Main listener loop ===
        reconnect_fail_count = 0
        last_reconnect_time = 0
        min_delay = 3
        max_delay = 60

        while not stop_event.is_set():
            try:
                time.sleep(min_delay)
                if not client.is_connected():
                    reconnect_fail_count += 1
                    # Exponential backoff
                    delay = min(max_delay, min_delay * int(math.pow(2, reconnect_fail_count)))
                    now = time.time()
                    if now - last_reconnect_time < delay:
                        continue
                    last_reconnect_time = now
                    _logger.warning(f"[{dbname}] Attempting reconnect to {broker_data['name']}...")

                    try:
                        client.reconnect()
                        client._subscribed = False
                        _logger.info(
                            f"[{dbname}] Reconnected to {broker_data['name']} (after {reconnect_fail_count} fails).")
                        reconnect_fail_count = 0  # Reset counter after success

                    except Exception as e:
                        _logger.error(f"[{dbname}] Reconnect failed: {e}")
                        # Notify after 5 consecutive fails
                        if reconnect_fail_count == 5:
                            with Registry(dbname).cursor() as cr:
                                env = api.Environment(cr, SUPERUSER_ID, {})
                                # Notify via bus (or send email if desired)
                                env['bus.bus']._sendone(
                                    dbname, ['mqtt_realtime'],
                                    {"error": f"Reconnect fail 5 times for broker {broker_data['name']}"}
                                )

            except Exception as e:
                _logger.error(f"[{dbname}] Error in MQTT loop for {broker_data['name']}: {e}")
                time.sleep(1)

        # Cleanup: Unsubscribe before disconnecting
        try:
            with Registry(dbname).cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                topic_names = self.get_subscribed_topics_for_broker(env, broker_id)

            if topic_names:
                client.unsubscribe(topic_names)
                _logger.info(f"Batch unsubscribed from {len(topic_names)} topics: {', '.join(topic_names)}")

                time.sleep(1)

        except Exception as e:
            _logger.error(f"[{dbname}] Error during unsubscribe in thread cleanup: {e}")

        client.loop_stop()
        client.disconnect()
        _logger.info(f"[{dbname}] Listener thread for broker {broker_data['name']} fully stopped and disconnected.")

    def action_review_subscription(self):
            self.ensure_one()
            action = self.env.ref('mqtt_integration.action_mqtt_subscription').read()[0]
            action.update({
                'domain': [
                    ('broker_id', '=', self.id),
                ],
                'context': {
                    'default_broker_id': self.id,
                }
            })
            return action

    @api.model
    def auto_start_all_listeners(self):
        """Check & auto start all connected brokers, listener runs or stops after service starts."""
        brokers = self.search([
            ('status', '=', 'connect'),
            ('listener_status', 'in', ['run', 'stop'])
        ])
        for broker in brokers:
            # If the broker does not have a listener thread running (due to just restarting), start again
            # Condition: check RAM variable/dict broker_threads
            if broker.id not in broker_threads or not broker_threads[broker.id].is_alive():
                _logger.info(f"Auto start listener for broker: {broker.name}")
                broker.action_start_listener()
            else:
                _logger.info(f"Broker {broker.name} already has active listener thread.")

    @api.model
    def _cron_broker_listener_auto_start(self):
        """Cron job to auto start all connection brokers"""
        for broker in self:
            try:
                if broker.status != 'connect' and broker.auto_reconnect:
                    broker.action_reconnect()
                broker.auto_start_all_listeners()
            except Exception as e:
                _logger.error(f"Error auto start listener for broker {broker.name}: {e}")
                pass
        _logger.info("Cron job to auto start all connected brokers completed.")
        return True

    # Basic method when Odoo start
    @api.model
    def _register_hook(self):
        res = super()._register_hook()
        self.auto_start_all_listeners()
        return res
