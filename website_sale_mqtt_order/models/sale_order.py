# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    mqtt_status = fields.Selection([
        ('draft', 'Draft'),
        ('accepted', 'Accepted'),
        ('preparing', 'Preparing'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered')
    ], string='MQTT Order Status', default='draft', tracking=True)

    mqtt_publish_fail_count = fields.Integer(string='MQTT Publish Failures', default=0)
    mqtt_last_publish_error = fields.Char(string='Last MQTT Error')

    def _prepare_mqtt_order_payload(self):
        self.ensure_one()
        items = []
        for line in self.order_line.filtered(lambda l: not l.display_type and l.product_uom_qty > 0):
            items.append({
                'product_id': line.product_id.id,
                'product_name': line.product_id.display_name,
                'quantity': line.product_uom_qty,
            })
        payload = {
            'order_id': self.id,
            'name': self.name,
            'partner_id': self.partner_id.id,
            'customer': self.partner_id.display_name,
            'items': items,
            'amount_total': self.amount_total,
            'currency': self.currency_id.name,
        }
        return payload

    def _mqtt_get_brand_and_topics(self):
        ICP = self.env['ir.config_parameter'].sudo()
        brand = ICP.get_param('website_sale_mqtt_order.brand_name', default='brandname')
        topic_orders = ICP.get_param('website_sale_mqtt_order.topic_orders', default=f"{brand}/orders")
        topic_status = ICP.get_param('website_sale_mqtt_order.topic_status', default=f"{brand}/status")
        broker_id = int(ICP.get_param('website_sale_mqtt_order.broker_id', default='0') or 0)
        return brand, topic_orders, topic_status, broker_id

    def _publish_order_to_mqtt(self):
        for order in self:
            brand, topic_orders, topic_status, broker_id = order._mqtt_get_brand_and_topics()
            if not broker_id:
                _logger.error('MQTT Broker not configured for website_sale_mqtt_order')
                order.write({'mqtt_last_publish_error': 'Broker not configured', 'mqtt_publish_fail_count': order.mqtt_publish_fail_count + 1})
                continue
            payload = order._prepare_mqtt_order_payload()
            try:
                sub = self.env['mqtt.subscription'].sudo().create({
                    'name': f"Order {order.name} publish",
                    'broker_id': broker_id,
                    'topic_id': self.env['mqtt.topic'].sudo().search([('name', '=', topic_orders), ('broker_id', '=', broker_id)], limit=1).id or False,
                    'direction': 'outgoing',
                    'format_payload': 'json',
                    'payload': json.dumps(payload),
                    'qos': 0,
                    'retain': False,
                    'status': 'subscribe',
                })
                if not sub.topic_id:
                    topic = self.env['mqtt.topic'].sudo().create({'name': topic_orders, 'broker_id': broker_id, 'status': 'confirm'})
                    sub.write({'topic_id': topic.id})
                sub.action_publish_message()
                order.write({'mqtt_last_publish_error': False, 'mqtt_publish_fail_count': 0})
            except Exception as e:
                _logger.exception('Failed to publish order %s to MQTT: %s', order.name, e)
                order.write({'mqtt_last_publish_error': str(e), 'mqtt_publish_fail_count': order.mqtt_publish_fail_count + 1})

    def action_confirm(self):
        res = super().action_confirm()
        try:
            self._publish_order_to_mqtt()
        except Exception as e:
            _logger.error('MQTT publish error post-confirm: %s', e)
        return res
