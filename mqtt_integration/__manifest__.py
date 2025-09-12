# -*- coding: utf-8 -*-
{
    'name' : 'MQTT Integration',
    'version': '18.2.0',
    'summary' : 'Technical Module for MQTT',
    'description': """
MQTT Integration for Odoo
====================
Integrates MQTT protocol into Odoo for connecting with IoT devices and MQTT services.

Features:
- Manage connections to MQTT Brokers
- Subscribe/monitor MQTT topics
- Send and receive MQTT message
- Store communication history
- Support automatic message transmission

Applications:
- IoT device monitoring
- Sensor data collection
- Integration with automation systems

Requirements: paho-mqtt
    """,
    'category': 'Extra Tools',
    'author' : 'Doan Man',
    'website': 'http://www.init.vn/',
    'depends' : ['base', 'mail'],
    'external_dependencies': {
        'python': ['paho']
    },
    'images' : [
        'static/description/banner.png',
        'static/description/mqtt_architecture.png',
        'static/description/mqtt_features.png',
        'static/description/mqtt_interface.png',
    ],
    'data' : [
        'security/ir.model.access.csv',
        'views/mqtt_broker_views.xml',
        'views/mqtt_subscription_views.xml',
        'views/mqtt_topic_views.xml',
        'views/mqtt_message_history_views.xml',
        'views/mqtt_metadata_views.xml',
        'views/mqtt_metadata_value_views.xml',
        'data/cron.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'post_init_hook': '_post_init_hook',
    'uninstall_hook': '_uninstall_hook',
    'post_load': '_auto_start_mqtt',
    'assets': {},
    'license': 'GPL-3',
}