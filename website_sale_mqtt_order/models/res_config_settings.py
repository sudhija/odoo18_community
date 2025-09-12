# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    website_sale_mqtt_brand = fields.Char(string='Brand Name', config_parameter='website_sale_mqtt_order.brand_name', default='brandname')
    website_sale_mqtt_topic_orders = fields.Char(string='Orders Topic', config_parameter='website_sale_mqtt_order.topic_orders')
    website_sale_mqtt_topic_status = fields.Char(string='Status Topic', config_parameter='website_sale_mqtt_order.topic_status')
    website_sale_mqtt_broker_id = fields.Many2one('mqtt.broker', string='MQTT Broker', config_parameter='website_sale_mqtt_order.broker_id')

    @api.model
    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('website_sale_mqtt_order.brand_name', self.website_sale_mqtt_brand)
        self.env['ir.config_parameter'].sudo().set_param('website_sale_mqtt_order.topic_orders', self.website_sale_mqtt_topic_orders)
        self.env['ir.config_parameter'].sudo().set_param('website_sale_mqtt_order.topic_status', self.website_sale_mqtt_topic_status)
        self.env['ir.config_parameter'].sudo().set_param('website_sale_mqtt_order.broker_id', self.website_sale_mqtt_broker_id.id)
