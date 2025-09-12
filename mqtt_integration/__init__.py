# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID
from odoo.modules.registry import Registry
from . import models
from . import tools
from . import utils
import logging

_logger = logging.getLogger(__name__)

# Get a list of active databases
registries = Registry.registries.d


def _post_init_hook(env):
    """Hook runs after the first module installation"""
    brokers = env['mqtt.broker'].search([])
    for broker in brokers:
        broker.auto_start_all_listeners()


def _uninstall_hook(env):
    """Hook runs before module uninstall"""
    for db_name, registry_obj in registries.items():
        try:
            with registry_obj.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                if 'mqtt.broker' in env:
                    brokers = env['mqtt.broker'].search([])
                    for broker in brokers:
                        broker.action_disconnect()
                        broker.action_stop_listener()
                    cr.commit()
                    _logger.info(f"Auto-stop all MQTT service for database {db_name} successfully.")

        except Exception as e:
            _logger.error(f"Error Auto-stop all MQTT service for database {db_name}: {e}")


def _auto_start_mqtt():
    """
        If you want to automatically “scan”
            and restart the listener for each DB when Odoo starts (multi-DB, multi-tenancy), use this function.
        When using multi-DB, call at _register_hook or where needed.
    """
    for db_name, registry_obj in registries.items():
        try:
            with registry_obj.cursor() as cr:
                env = api.Environment(cr, SUPERUSER_ID, {})
                if 'mqtt.broker' in env:
                    _logger.info(f"Auto-starting MQTT service for database {db_name}")
                    brokers = env['mqtt.broker'].search([])
                    for broker in brokers:
                        broker.action_start_listener()
                    cr.commit()
        except Exception as e:
            _logger.error(f"Unable to start MQTT service for database {db_name}: {e}")
