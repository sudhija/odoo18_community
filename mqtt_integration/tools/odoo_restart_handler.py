# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
import atexit
import logging
import time

_logger = logging.getLogger(__name__)

def stop_mqtt_on_shutdown():
    """Function called when Odoo shuts down"""
    start_time = time.time()
    _logger.info("Shutting down Odoo, stopping MQTT service...")

    # Loop through all active databases
    registries = Registry.registries.d
    for db_name, registry_obj in registries.items():
        try:
            with registry_obj.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                if 'mqtt.broker' in env:
                    service = env['mqtt.broker'].search([], limit=1)
                    if service and service.listener_status == 'run':
                        _logger.info(f"Stopping MQTT Broker service for database {db_name}")
                        env['mqtt.broker'].action_stop_listener()
                        cr.commit()
        except Exception as e:
            _logger.error(f"Error stopping MQTT Broker service for database {db_name}: {e}", exc_info=True)

    elapsed_time = time.time() - start_time
    _logger.info(f"MQTT Broker service shutdown completed in {elapsed_time:.2f} seconds")


# Register MQTT Broker stop function when Odoo exits
atexit.register(stop_mqtt_on_shutdown)