MQTT Instance
---

## 1. Overview

**MQTT Integration & Listener** is a robust system to integrate MQTT (Message Queuing Telemetry Transport) into Odoo.  
This module enables Odoo to **communicate in real-time with IoT devices and external services** via MQTT brokers:
- Manage brokers, topics, subscriptions, messages, user properties
- Listen and handle messages automatically using background listener threads/services
- Log all message histories and properties according to the MQTT v5 standard
- Auto start/stop listeners according to Odoo's lifecycle, fully compatible with multi-database environments

---

## 2. System Architecture & Data Flow

### 2.1. Core Components

| Component            | Model/Class                               | Key Functionality                                  |
|----------------------|-------------------------------------------|----------------------------------------------------|
| **Broker**           | `mqtt.broker`                             | Broker management, connect/disconnect, listener management, status tracking |
| **Topic**            | `mqtt.topic`                              | Topic management per broker                        |
| **Subscription**     | `mqtt.subscription`                       | Register/unregister topic subscriptions, manage status |
| **Message History**  | `mqtt.message.history`                    | Log incoming/outgoing messages, link to properties |
| **User Property**    | `mqtt.metadata` and `mqtt.metadata.value` | Store MQTT v5 user properties per message          |
| **Listener Service** | (thread/service)                          | Background thread listens to broker, processes messages, logs history |
| **Hook & Cron**      | `__init__.py` + cron.xml                  | Auto start/stop listeners on install, uninstall, or Odoo restart |

### 2.2. Operation Flow

1. **Broker Setup:**  
   - Create and configure one or more MQTT brokers (`mqtt.broker`) with host, port, client_id, etc.
2. **Topic Management:**  
   - Create topics for each broker, only `status='confirm'` topics can be subscribed.
3. **Subscription Management:**  
   - Register/unregister subscriptions for each topic.  
   - Each subscription links a broker and topic, tracks status, payload, payload format (json, plaintext, hex, base64), QoS, retain, etc.
4. **Listener Service:**  
   - When a broker is connected and the listener started, Odoo spawns a background thread that listens for all subscribed topics.  
   - Received messages are processed, history is logged, properties are extracted, and notifications are sent via Odoo's bus.
5. **Message Processing:**  
   - Messages can be sent from Odoo to MQTT (`action_publish_message`),  
   - Received messages are automatically logged in `mqtt.message.history`.
6. **User Property & Metadata:**  
   - Automatically records all MQTT v5 properties of each message in `mqtt.metadata` and `mqtt.metada.value` for auditing and traceability.
7. **Lifecycle & Auto Recovery:**  
   - Uses Odoo hooks (`_post_init_hook`, `_uninstall_hook`, `_auto_start_mqtt`) and a periodic cron job to ensure all listeners are always running in line with broker status, even after Odoo restarts or module (un)installs.

---

## 3. Component Details

### 3.1. MQTT Broker (`mqtt.broker`)
- **Key fields:** name, client_id, url_scheme, host, port, username/password, keepalive, status, listener_status
- **Key actions:**  
  - `action_connection`, `action_disconnect`, `action_reconnect`  
  - `action_start_listener`, `action_stop_listener`  
  - `action_renew_broker` (reset broker to draft)
- Unique `client_id` is auto-generated per broker.
- **Auto recovery:** When Odoo starts (or via cron), all brokers with status "connect" and listener_status "run"/"stop" are auto-restarted as listener threads.
- **Thread safety:** RAM-level thread tracking prevents duplicate listeners.
- All actions are thoroughly logged for debugging.

### 3.2. Topic (`mqtt.topic`)
- Linked to a broker, status (`draft`/`confirm`), creator, QoS, all MQTT v5 flags.
- Only topics with `status='confirm'` are eligible for subscription.

### 3.3. Subscription (`mqtt.subscription`)
- Links broker, topic, status (`subscribe`/`unsubscribe`/`fail`), direction (`incoming`/`outgoing`), format_payload, default payload, QoS, retain, etc.
- **Key actions:**  
  - `action_subscribe`, `action_unsubscribe`, `action_renew_subscription`, `action_publish_message`  
  - Payload validation and formatting tools for debugging.
- **Validation:** Payload is checked to match the specified format.
- On subscribe/unsubscribe, the listener is auto-restarted, so threads instantly pick up new topics.

### 3.4. Message History (`mqtt.message.history`)
- Logs all messages (incoming/outgoing), including broker, subscription, topic, format, payload, QoS, retain, timestamp.
- **Auto-generated display_name** (Broker - Topic - timestamp) for easy reference.
- Complete audit/history tracking.

### 3.5. User Property (`mqtt.metadata` and `mqtt.metadata.value`)
- Records all MQTT v5 message properties: key, value, content_type, format_payload, expiry, response_topic, correlation_data, subscription_identifier, etc.
- Linked to each topic/message/history.
- Clear UI for querying properties.

### 3.6. Listener Service
- Background thread with `loop_start`, auto-reconnect, exponential backoff, and reconnect failure logging.
- Stopping Odoo/module will stop all listeners, preventing resource leakage.
- Listener can be (re)started manually or automatically (via cron/hook).

---

## 4. Lifecycle Management & Hooks

- **Odoo Lifecycle:**
  - On module install (`_post_init_hook`): auto-start listeners for all brokers currently connected.
  - On uninstallation (`_uninstall_hook`): auto-stop/cleanup listeners for all brokers.
  - On Odoo restart:  
    - `_auto_start_mqtt` hook (via manifest or called manually) + cron (every 10 min) to ensure listeners are never left "offline."
  - `odoo_restart_handler.py` uses `atexit` to clean up listeners on abrupt Odoo shutdown.

---

## 5. Usage Flow (Practical API/UX)

### A. Broker Setup & Connection
```python
broker = env['mqtt.broker'].create({
    'name': 'My Broker',
    'host': 'broker.emqx.io',
    'port': 1883,
    # ...
})
broker.action_connection()
broker.action_start_listener()
```

### B. Topic Creation & Confirmation
```python
topic = env['mqtt.topic'].create({
    'name': 'my/topic',
    'broker_id': broker.id,
})
topic.action_confirm()
```

### C. Register Subscription
```python
sub = env['mqtt.subscription'].create({
    'broker_id': broker.id,
    'topic_id': topic.id,
    # ...
})
sub.action_subscribe()

```

### D. Publish Message (Odoo → MQTT)
```python
sub.action_publish_message()
```

### E. Receive Message (MQTT → Odoo)
- Listener thread receives the message and logs it in mqtt.message.history, with all user properties in mqtt.user.property.

## 6. Auto Recovery & Monitoring
- **Auto Start Listener**:
On Odoo restart, all brokers with the status "connect" will automatically have listeners restarted via hook/cron.
- **Cron** (default: every 10 minutes, configurable):
```python
model._cron_broker_listener_auto_start()
```
- **Extensive logging** for all actions and errors, facilitating debugging and profiling.
- **Activity Tracking**:
Track uptime, status, and detect inactivity for brokers/listeners.

## 7. Best Practices & Security
- **Use unique client_id per broker** (module auto-generates).
- **Only subscribe to topics in "confirmed" status.**
- **Validate payload format before sending/receiving.**
- **Monitor logs and status for early error detection.**
- **Store credentials securely in DB; use HTTPS for Odoo and enable TLS/SSL for brokers whenever possible.**
- **Restrict client user permissions on the broker to only the necessary publish/subscribe topics.**

## 8. Debugging & Performance
- **View message history (incoming/outgoing) and detailed properties via UI.**
- **Utilize Odoo logging to trace issues and performance.**
- **If needing a quick restart, use the broker UI's Stop/Start Listener buttons.**

## 9. Extension & Integration
- **Inherit/extend models to add IoT/automation logic.**
- **Integrate with Odoo automation, rules, workflow, etc. via standard API.**
- **All actions use @api.model/@api.multi for controller/service compatibility.**

## 10. Deployment
1. Install the Python package `paho-mqtt`.
2. Deploy this module into Odoo, update the app list.
3. Create brokers, topics, and subscriptions via the UI.
4. Test subscribing/publishing with real brokers or MQTTX/EMQX tools.
5. Monitor logs and history to verify the correct operation.

## 11. References
- [Paho MQTT Python](https://www.eclipse.org/paho/index.php?page=clients/python/index.php)
- [MQTT v5.0 Spec](https://docs.oasis-open.org/mqtt/mqtt/v5.0/mqtt-v5.0.html)
- [Odoo Documentation](https://www.odoo.com/documentation)
- [Threading in Python](https://docs.python.org/3/library/threading.html)
- [IoT Protocols Overview](https://www.a1.digital/knowledge-hub/iot-protocols-a-comprehensive-guide/)

_This documentation accurately reflects the flow, thread logic, data models, and resource management hooks of the current module code. For PDF export, visual diagrams, or more advanced use cases, please request further support!_

---
