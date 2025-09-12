"""
    Ultimate Utility Function Collection for Python/Odoo Projects
    =======================================================================

    🔥 **Overview**
    This file aggregates utility functions designed with the following principles:
    - **Simplify** the development process and optimize your codebase.
    - **Maximize reusability** across all parts of the project: Odoo modules, standalone scripts, backend automation, etc.
    - **Standardize** common processing logic to reduce code duplication, minimize bugs, and ease maintenance & refactoring.
    - **Easily extensible**: Any logic or helper frequently used can be added here for the whole team to leverage.

    🚀 **Benefits**
    - Import once, use anywhere in your project.
    - Clear, well-structured, with a docstring for every function.
    - Acts as a **single source of truth** for advanced utilities, common tasks, or special business logic that may expand over time.
    - Compatible with Odoo, pure Python scripts, microservices, or any Python environment.

    🧩 **Usage Example**
        from .utils import function_name_1, function_name_2
        result = function_name_1(params)

    📚 Contribution Guidelines
    When adding a new function, provide a clear docstring explaining its purpose and usage.
    Avoid bloating with niche helpers; keep only functions that are truly generic, frequently reused, or critical to core business logic.
    Developed by Dev Team — “Write once, benefit the whole project!”
"""

def broker_client(client_id, clean_session, protocol, **kwargs):
    """
    Create and configure a Paho MQTT client with advanced options.

    Args:
        client_id (str): Unique client identifier.
        protocol: MQTT protocol version (mqtt.MQTTv31, mqtt.MQTTv311, or mqtt.MQTTv5).
        clean_session (bool, optional):
            - Required for MQTTv31/v311 (default: True).
            - Must not be True when using MQTTv5.
        **kwargs: Additional client configuration options.
            - transport (str): 'tcp' or 'websockets'. Default is 'tcp'.
            - keepalive (int): Keepalive interval in seconds. Default is 60.
            - socket_timeout (int): Socket timeout in seconds. Default is 60.
            - reconnect_delay (tuple): (min_delay, max_delay) for reconnecting.

    Returns:
        mqtt.Client: Configured MQTT client instance.

    Raises:
        ValueError: If invalid parameters are provided.
        RuntimeError: If client creation fails.

    Notes:
        - When protocol is mqtt.MQTTv5 do NOT provide 'clean_session'.
        - When protocol is mqtt.MQTTv311 or mqtt.MQTTv31, you SHOULD provide 'clean_session'.
    """
    import paho.mqtt.client as mqtt

    if not isinstance(client_id, str) or not client_id.strip():
        raise ValueError("client_id must be a non-empty string")

    if protocol not in ['MQTTv31', 'MQTTv311', 'MQTTv5']:
        raise ValueError("protocol must be MQTTv31, MQTTv311, or MQTTv5")
    else:
        pr_clean_session = clean_session or False
        if protocol == 'MQTTv31':
            protocol = mqtt.MQTTv31
        elif protocol == 'MQTTv311':
            protocol = mqtt.MQTTv311
        elif protocol == 'MQTTv5':
            protocol = mqtt.MQTTv5
            pr_clean_session = None
        else:
            raise ValueError("Unsupported protocol")

    # Set up default options
    config = {
        'protocol': protocol,
        'transport': 'tcp',
        'keepalive': 60,
        'socket_timeout': 60,
        'reconnect_delay': (1, 120),
    }
    config.update(kwargs)

    try:
        # Do NOT provide clean_session for MQTTv5
        if protocol == mqtt.MQTTv5:
            client = mqtt.Client(
                client_id=client_id.strip(),
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                protocol=protocol,
                transport=config['transport'],
            )
        else:
            # For MQTTv311 or MQTTv31, clean_session is required
            client = mqtt.Client(
                client_id=client_id.strip(),
                callback_api_version=mqtt.CallbackAPIVersion.VERSION2,
                protocol=protocol,
                clean_session=pr_clean_session,
                transport=config['transport'],
            )

        client.reconnect_delay_set(*config['reconnect_delay'])
        client.socket_timeout = config['socket_timeout']
        client.keepalive = config['keepalive']

        return client

    except Exception as e:
        raise RuntimeError(f"Error creating MQTT client: {e}")

def get_first_or_zero(val):
    """
    Utility function to safely extract the first element from a list, tuple, or bytes object.
    - If `val` is a list, tuple, or bytes, returns the first element if available; otherwise, returns 0.
    - If `val` is any other truthy value (int, str, etc.), returns it as is.
    - If `val` is None or falsy, returns 0.

    Useful for handling MQTT property values that can be sequences or scalars.

    Args:
        val (Any): The input value (sequence, int, str, etc.)

    Returns:
        Any: The first element, or the value itself, or 0 if empty.
    """
    if isinstance(val, (list, tuple, bytes)):
        return val[0] if val else 0
    elif val:
        return val
    return 0
