# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import datetime as py_datetime
import pytz
import logging

_logger = logging.getLogger(__name__)

IST = pytz.timezone('Asia/Kolkata')

class RestaurantTable(models.Model):
    _inherit = 'restaurant.table'

    color_status = fields.Selection([
        ('green', 'Available'),
        ('red', 'Occupied'),
        ('yellow', 'Future Booking'),
    ], string='Color Status', compute='_compute_color_status', store=False,
       help='Computed color for frontend UI (green=available, red=occupied, yellow=future)')

    def _to_dt(self, value):
        """Convert strings/datetimes into python datetime (IST aware)."""
        if not value:
            return None
        if isinstance(value, str):
            try:
                dt = py_datetime.strptime(value[:19], "%Y-%m-%d %H:%M:%S")
            except Exception:
                try:
                    dt = py_datetime.strptime(value[:16], "%Y-%m-%d %H:%M")
                except Exception:
                    return None
            return IST.localize(dt)
        if isinstance(value, py_datetime):
            # if naive, localize to IST
            return value if value.tzinfo else IST.localize(value)
        return None

    def _compute_color_status(self):
        """Compute status per table by searching related reservations."""
        Reservation = self.env['table.reservation']
        now = py_datetime.now(IST)  # current IST time

        for table in self:
            color = 'green'

            resv = Reservation.search([
                '|',
                ('booked_tables_ids', 'in', table.id),
                ('table_id', '=', table.id),
                ('state', '=', 'reserved')
            ])

            for r in resv:
                # Try datetime fields
                start = self._to_dt(getattr(r, 'start_time', None))
                end = self._to_dt(getattr(r, 'end_time', None))

                # If missing, try date + time fields
                if not start or not end:
                    try:
                        date_str = str(r.date)
                        s_at = getattr(r, 'starting_at', None)
                        e_at = getattr(r, 'ending_at', None)
                        if date_str and s_at and e_at:
                            start = IST.localize(py_datetime.strptime(f"{date_str} {s_at}", "%Y-%m-%d %H:%M"))
                            end = IST.localize(py_datetime.strptime(f"{date_str} {e_at}", "%Y-%m-%d %H:%M"))
                    except Exception:
                        start, end = None, None

                if start and end:
                    if start <= now <= end:
                        color = 'red'
                        break
                    elif start > now and color != 'red':
                        color = 'yellow'

            table.color_status = color
            _logger.debug(
                "Table %s computed color_status=%s (found %d reservations, now=%s)",
                table.id, color, len(resv), now
            )
