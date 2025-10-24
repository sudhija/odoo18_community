POS Table Reservation Extended
------------------------------------
Install this module alongside the original Cybrosys 'table_reservation_on_website' module.
- Adds color status (green/red/yellow) to tables (computed)
- Adds a website dashboard at /pos_manager/dashboard (user must be logged in)
- Includes responsive CSS and a small polling JS to refresh statuses every 20s
Notes:
- This module intentionally _inherits_ models and templates; it does not modify Cybrosys code directly.
- Requires: table_reservation_on_website, website, pos, restaurant
