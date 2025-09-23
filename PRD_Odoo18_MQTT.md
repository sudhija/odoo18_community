### Product Requirements Document (PRD): Odoo 18 Community – Online Ordering with MQTT Integration

## 1) Introduction & Background
- **Platform**: Odoo 18 Community with `website`, `website_sale` (eCommerce), and custom MQTT integration.
- **Integration**: External MQTT broker (e.g., EMQX or Mosquitto).
- **Goal**: When a customer places an order on the Odoo website, send order details to a robot via MQTT and receive live status updates back to Odoo to display in the customer’s account.

## 2) Objectives
- **Online Ordering**: Enable customers to order food/products via the Odoo 18 website.
- **Outbound MQTT**: Publish order details as JSON to topic `brandname/orders`.
- **Inbound MQTT**: Subscribe to `brandname/status` to receive status updates.
- **Status Persistence**: Store order status against the corresponding Sales Order in Odoo.
- **Customer Visibility**: Show order history and live status on “My Orders” page with real-time-ish updates.

## 3) Stakeholders
- **Customers**: Place and track orders from the website.
- **Website Users**: Authenticated customers managing orders.
- **Odoo Admin**: Configures products, MQTT settings, monitors operations.
- **Robot/IoT System**: Consumes orders and publishes status.
- **MQTT Broker**: Message transport backbone.

## 4) Functional Requirements
- **FR-1 Checkout Capture**
  - Use `website_sale` checkout flow.
  - Capture: order ID, customer ID, lines (product name, product_id, quantity, price), requested notes, delivery/pickup details.
- **FR-2 Order Publication to MQTT**
  - On order confirmation: publish JSON to `brandname/orders`.
  - Payload fields (minimum):
    - `order_id` (Odoo SO name or ID)
    - `customer_ref` (partner id or email)
    - `lines`: array of `{product_id, product_name, quantity}`
    - `timestamp` (UTC ISO 8601)
    - `channel` = "web"
  - Example:
    ```json
    {
      "order_id": "SO02341",
      "customer_ref": "john.doe@example.com",
      "lines": [
        {"product_id": 101, "product_name": "Chicken Shawarma", "quantity": 2},
        {"product_id": 55, "product_name": "Mango Juice", "quantity": 1}
      ],
      "timestamp": "2025-09-08T12:34:56Z",
      "channel": "web"
    }
    ```
- **FR-3 Subscribe to Status Topic**
  - Subscribe to `brandname/status`.
  - Expected message schema:
    - `order_id`
    - `status` ∈ {"accepted","preparing","ready","delivered","rejected","failed"}
    - Optional: `eta_minutes`, `note`, `robot_job_id`, `timestamp`.
  - Example:
    ```json
    {
      "order_id": "SO02341",
      "status": "preparing",
      "eta_minutes": 8,
      "timestamp": "2025-09-08T12:36:00Z"
    }
    ```
- **FR-4 Status Mapping & Persistence**
  - Map inbound MQTT status to a new Odoo order status field:
    - Use a custom field on `sale.order` (e.g., `x_robot_status`).
    - Maintain a status history model (e.g., `robot.order.status.log`) with timestamps.
  - Update only if `order_id` matches an existing order.
- **FR-5 UI: Customer “My Orders”**
  - Extend website account area to show:
    - Order list with current `x_robot_status`, last updated time, and ETA.
    - Order detail page with line items and a status timeline (accepted → preparing → ready → delivered).
  - Support soft real-time refresh (e.g., AJAX polling every 5–10s).
- **FR-6 Admin Configuration**
  - Odoo Settings page to store:
    - MQTT broker host, port, TLS, username/password, base topic prefix (`brandname`).
    - QoS (0/1), retain flag for orders, client ID prefix.
    - Connection test button.
- **FR-7 Reliability**
  - Retry publishing on transient failures with exponential backoff.
  - Local queue of outbound messages if broker is unavailable; drain on reconnect.
  - Idempotent consumption (ignore duplicate statuses).
- **FR-8 Security & Validation**
  - Validate payloads before publish.
  - Verify inbound messages contain a known `order_id`.
  - Option to restrict accepted status source via broker auth or message signing.

## 5) Non-Functional Requirements
- **NFR-1 Real-time**: End-to-end status latency target ≤ 5 seconds P50, ≤ 10 seconds P95.
- **NFR-2 Security**: Support MQTT over TLS; broker auth required; credentials stored securely.
- **NFR-3 Scalability**: Handle 200 concurrent orders and 20 msg/s sustained.
- **NFR-4 Availability**: Degraded mode with queued outbound messages if broker down.
- **NFR-5 Observability**: Logs for publish/subscribe, connection events, retries; admin dashboard counters.
- **NFR-6 Maintainability**: Configurable topics, decoupled module (`mqtt_integration`) with clear interfaces.

## 6) System Workflow / User Journey
1. Customer browses Odoo website and adds items to cart.
2. Customer checks out and confirms the order (Sales Order created/confirmed).
3. Odoo publishes JSON payload to `brandname/orders`.
4. Robot/IoT system consumes the message and starts processing.
5. Robot publishes status updates to `brandname/status` with the same `order_id`.
6. Odoo MQTT subscriber updates `x_robot_status` and logs the status history.
7. Customer views “My Orders” to see live status; page auto-refreshes periodically.
8. When status becomes `delivered`, order is marked complete in UI.

### Sequence Diagram (Mermaid)
```mermaid
sequenceDiagram
    autonumber
    participant C as Customer (Web)
    participant OW as Odoo Website
    participant OM as Odoo MQTT Module
    participant MB as MQTT Broker
    participant R as Robot/IoT

    C->>OW: Place order (checkout confirm)
    OW->>OW: Create/confirm Sales Order (SO)
    OW->>OM: Trigger publish event with SO data
    OM->>MB: Publish brandname/orders {order_id, lines, ...}
    MB-->>R: Deliver order message
    R->>R: Accept and process order
    R->>MB: Publish brandname/status {order_id, status=accepted}
    MB-->>OM: Deliver status message
    OM->>OW: Update SO.x_robot_status=accepted
    C->>OW: View "My Orders"
    OW-->>C: Show status = accepted (auto-refresh)
    loop Until delivered
      R->>MB: Publish status {preparing/ready/..}
      MB-->>OM: Deliver status
      OM->>OW: Update SO + history
      OW-->>C: Show updated status
    end
    R->>MB: Publish status {delivered}
    MB-->>OM: Deliver final status
    OM->>OW: Persist delivered; close tracking
    OW-->>C: Show delivered
```

## 7) Assumptions & Constraints
- **Assumptions**
  - Odoo 18 Community, `website_sale` enabled and configured.
  - External MQTT broker (EMQX/Mosquitto) reachable over the network.
  - Robot can consume the defined JSON and publishes timely status updates.
  - Customer authentication required to view order status/history.
- **Constraints**
  - Internet connectivity for broker communication.
  - Broker credentials/TLS certs provided by ops/IaC.
  - Topic namespace fixed to `brandname/*` but `brandname` is configurable.

## 8) Data Model & Topic Design
- **Topics**
  - Orders publish: `brandname/orders`
  - Status subscribe: `brandname/status`
- **Odoo Fields**
  - `sale.order.x_robot_status` (selection)
  - `robot.order.status.log` with fields: `order_id` (m2o to SO), `status`, `note`, `eta_minutes`, `timestamp`.

## 9) Error Handling & Edge Cases
- Unknown `order_id` in inbound message → log warning, discard or park in DLQ table.
- Duplicate status messages → ignore based on `(order_id, status, timestamp)` uniqueness.
- Broker down on publish → enqueue; retry with backoff up to a max window (e.g., 30 min).
- Customer cancels order → publish cancellation message (optional future extension).
- Large orders or long prep times → keep UI polling; show last updated time.

## 10) Configuration & Deployment
- Admin menu: MQTT Settings (host, port, TLS toggle, username, password, QoS, retain, base topic).
- Health check: “Test Connection” button attempts connect, publish to a test topic, and subscribe.
- Service: Long-lived MQTT client within Odoo worker with reconnect strategy.
- Access control: Only internal users with specific group can change MQTT settings.

## 11) Acceptance Criteria
- **AC-1 Publish on Confirm**: When a Sales Order is confirmed, a JSON payload is published to `brandname/orders` with accurate product names and quantities.
- **AC-2 Status Handling**: When the robot publishes to `brandname/status`, Odoo updates the corresponding `sale.order.x_robot_status` within 5 seconds (P50) and 10 seconds (P95).
- **AC-3 UI Visibility**: The “My Orders” page shows current status and updates without manual page reload within 10 seconds.
- **AC-4 Resilience**: If the broker is unavailable, the system queues outbound messages and successfully publishes them once the broker is back, with no data loss.
- **AC-5 Security**: MQTT connections require authentication; TLS works when configured; credentials are not exposed in logs/UI.
- **AC-6 Observability**: Admin can see connection status, last publish/subscribe timestamps, and retry counters.

## 12) Out of Scope (Initial Phase)
- Payments, delivery logistics, or kitchen display systems beyond robot status.
- Websocket/SSE live push to browser (AJAX polling suffices initially).
- Advanced orchestration (multi-robot assignment) or priority routing.

## 13) Future Enhancements
- Websocket/SSE for lower-latency browser updates.
- Acknowledgement/receipt tracking for robot acceptance with SLAs.
- Message signing (HMAC) to authenticate producer system.
- Per-line item robot assignment and partial fulfillment statuses.


