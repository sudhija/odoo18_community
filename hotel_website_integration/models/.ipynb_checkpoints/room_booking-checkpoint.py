from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta, date as pydate

class HotelBooking(models.Model):
    # Align with existing backend by extending room.booking (no extra fields required here)
    _inherit = "room.booking"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    payment_transaction_id = fields.Many2one('payment.transaction', string="Payment Transaction")
    room_id = fields.Many2one('hotel.room', string='Room', required=True)

    # 🧱 SQL constraint to prevent duplicate room bookings
    _sql_constraints = [
        (
            'unique_room_booking',
            'unique(room_id, sale_order_id, checkin_date, checkout_date)',
            'This room already has a booking for the same dates!'
        ),
    ]

    @api.model
    def create_reservation_from_sale_order(self, sale_order):
        """Create hotel reservations from a confirmed sale order containing rooms."""
        _logger.info(">>> create_reservation_from_sale_order triggered for SO %s", sale_order.name)

        for line in sale_order.order_line.filtered(lambda l: l.room_id):
            checkin = getattr(line, 'checkin_date', fields.Date.today())
            checkout = getattr(line, 'checkout_date', checkin + timedelta(days=1))

             # Normalize to date only
            checkin = fields.Date.to_date(checkin)
            checkout = fields.Date.to_date(checkout)
            
            # Check if a reservation for this line already exists
            existing_booking = self.search([
                ('sale_order_id', '=', sale_order.id),
                ('room_id', '=', line.room_id.id),
                ('checkin_date', '=', checkin),
                ('checkout_date', '=', checkout),
            ], limit=1)

            if existing_booking:
                _logger.info("Skipping duplicate booking for %s (SO %s)", line.room_id.name, sale_order.name)
                continue

            # Check availability
            if not line.room_id.is_available(checkin, checkout, line.product_uom_qty):
                _logger.warning('Room %s not available for SO %s', line.room_id.name, sale_order.name)
                continue

            # Create booking
            booking_vals = {
                'room_id': line.room_id.id,
                'partner_id': sale_order.partner_id.id,
                'checkin_date': checkin,
                'checkout_date': checkout,
                'guest_count': line.product_uom_qty,
                'sale_order_id': sale_order.id,
                'state': 'reserved',
                'price_total': line.price_total,
            }
            booking = self.create(booking_vals)
            _logger.info("Created booking ID %s for %s", booking.id, line.room_id.name)

        return True
        
    @api.model
    def create(self, vals):
        """Override create to prevent overlapping bookings at runtime."""
        checkin = vals.get('checkin_date')
        checkout = vals.get('checkout_date')
        room_id = vals.get('room_id')

        if checkin:
            checkin = fields.Date.to_date(checkin)
        if checkout:
            checkout = fields.Date.to_date(checkout)

        # Search for overlapping bookings
        overlapping = self.search([
            ('room_id', '=', room_id),
            ('checkin_date', '<', checkout),
            ('checkout_date', '>', checkin),
        ], limit=1)

        if overlapping:
            raise ValidationError(
                _("Room '%s' is already booked between %s and %s!") %
                (overlapping.room_id.name, overlapping.checkin_date, overlapping.checkout_date)
            )

        return super(HotelBooking, self).create(vals)
    

    @api.constrains('room_id', 'checkin_date', 'checkout_date')
    def _check_overlapping_bookings(self):
        """Prevent overlapping bookings for the same room."""
        for record in self:
            if not record.room_id or not record.checkin_date or not record.checkout_date:
                continue

            checkin = fields.Date.to_date(record.checkin_date)
            checkout = fields.Date.to_date(record.checkout_date)

            overlapping = self.search([
                ('id', '!=', record.id),
                ('room_id', '=', record.room_id.id),
                ('state', 'in', ['reserved', 'check_in', 'paid']),  # optional states that block availability
                ('checkin_date', '<', record.checkout_date),
                ('checkout_date', '>', record.checkin_date),
            ], limit=1)

            if overlapping:
                raise ValidationError(
                    _("Room '%s' is already booked between %s and %s!") %
                    (record.room_id.name, overlapping.checkin_date, overlapping.checkout_date)
                )


    @api.model
    def _link_reservation_to_invoice(self, reservation_id, invoice_id):
        """Link reservation to generated invoice."""
        reservation = self.browse(reservation_id)
        invoice = self.env['account.move'].browse(invoice_id)
        reservation.invoice_id = invoice.id
        reservation.state = 'invoiced'
        return True

    def _sync_payment_status(self):
        """Update reservation state based on payment transaction."""
        for booking in self:
            if booking.payment_transaction_id and booking.payment_transaction_id.state == 'done':
                booking.state = 'paid'
        return True

    
    
    