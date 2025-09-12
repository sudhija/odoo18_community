# -*- coding: utf-8 -*-
from odoo import models, api
import json
import logging

_logger = logging.getLogger(__name__)

class MQTTMessageHistory(models.Model):
    _inherit = 'mqtt.message.history'

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        try:
            for rec in records:
                self.env.cr.commit()
                self._handle_status_message(rec)
        except Exception as e:
            _logger.error('Error handling MQTT status message: %s', e)
        return records

    def _handle_status_message(self, history):
        if not history or not history.topic:
            return
        try:
            ICP = self.env['ir.config_parameter'].sudo()
            brand = ICP.get_param('website_sale_mqtt_order.brand_name', default='brandname')
            topic_status = ICP.get_param('website_sale_mqtt_order.topic_status', default=f"{brand}/status")
            if history.topic != topic_status:
                return
            payload = history.payload or ''
            data = json.loads(payload)
            order_id = data.get('order_id') or False
            status = (data.get('status') or '').lower()
            if not order_id or status not in {'accepted','preparing','ready','delivered'}:
                return
            order = self.env['sale.order'].sudo().browse(order_id)
            if not order.exists():
                _logger.warning('Status for unknown order id %s', order_id)
                return
            order.write({'mqtt_status': status})
        except Exception as e:
            _logger.error('Failed to process status message: %s', e)
