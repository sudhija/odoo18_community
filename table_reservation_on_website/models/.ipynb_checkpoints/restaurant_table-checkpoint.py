from odoo import models, fields, api
from datetime import datetime, timedelta


class RestaurantTable(models.Model):
    """ Inherit restaurant table for adding rate field and enhancements """
    _inherit = 'restaurant.table'

    rate = fields.Float(string="Amount", help="Amount for reservation of this table")

    is_show_field = fields.Boolean(
        string='Show field',
        compute='_compute_is_show_field',
        help='Depends on the field value field rate visibility is determined'
    )

    reservation_ids = fields.One2many(
        'table.reservation',
        'table_id',
        string="Reservations"
    )

    is_available = fields.Boolean(
        string="Available",
        compute="_compute_availability",
        store=True,
        help="Computed availability based on current time and reservations"
    )

    available_from = fields.Float(
        string="Available From (Hours, 24h)",
        default=10.0,
        help="Start hour for reservation (e.g., 10.0 = 10:00 AM)"
    )

    available_to = fields.Float(
        string="Available Until (Hours, 24h)",
        default=23.0,
        help="End hour for reservation (e.g., 23.0 = 11:00 PM)"
    )

    reservation_status = fields.Selection([
        ('available', 'Available'),
        ('occupied', 'Occupied'),
        ('future', 'Future Reservation')
    ], string="Reservation Status", compute='_compute_reservation_status', store=True)
    
    last_reservation_end = fields.Datetime(
        string="Reserved Until", 
        compute='_compute_reservation_status', 
        store=True
    )

    @api.depends('rate')
    def _compute_is_show_field(self):
        """ Show field if rate is greater than zero """
        for record in self:
            record.is_show_field = bool(record.rate and record.rate > 0)

    @api.depends('reservation_ids.start_time', 'reservation_ids.end_time')
    def _compute_reservation_status(self):
        now = fields.Datetime.now()
        for table in self:
            reservations = table.reservation_ids.filtered(
                lambda r: r.start_time and r.end_time and r.start_time <= now <= r.end_time
            )
            if reservations:
                table.reservation_status = 'occupied'
                table.last_reservation_end = max(reservations.mapped('end_time'))
            else:
                future_res = table.reservation_ids.filtered(
                    lambda r: r.start_time and r.start_time > now
                )
                if future_res:
                    table.reservation_status = 'future'
                    table.last_reservation_end = max(future_res.mapped('end_time'))
                else:
                    table.reservation_status = 'available'
                    table.last_reservation_end = False


    @api.depends('reservation_ids.start_time', 'reservation_ids.end_time')
    def _compute_availability(self):
        """Compute table availability based on current reservations."""
        now = fields.Datetime.now()
        for table in self:
            active_res = table.reservation_ids.filtered(
                lambda r: r.start_time and r.end_time and r.start_time <= now <= r.end_time
            )
            table.is_available = not bool(active_res)
