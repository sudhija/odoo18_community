# -*- coding: utf-8 -*-
from odoo import models, fields, api


class MQTTMetadataValue(models.Model):
    _name = 'mqtt.metadata.value'
    _description = 'MQTT Metadata values (User Property Values)'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    metadata_name = fields.Char(related='metadata_id.name', string="Metadata Name", store=True)
    key = fields.Char(string='Key', required=True)
    value = fields.Char(string='Value')
    timestamp = fields.Datetime(string='Timestamp', default=fields.Datetime.now, readonly=True)
    metadata_id = fields.Many2one('mqtt.metadata', string='Metadata')
    topic_id = fields.Many2one('mqtt.topic', string='Topic')

    @api.depends('metadata_id')
    def _compute_name(self):
        for rec in self:
            if rec.metadata_id:
                rec.name = rec.metadata_id.name or "Unknown Metadata Values Subscription"
            else:
                rec.name = "Incomplete Configuration"
