from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta, date as pydate

class HotelBooking(models.Model):
    # Align with existing backend by extending room.booking (no extra fields required here)
    _inherit = "room.booking"

    sale_order_id = fields.Many2one('sale.order', string="Sale Order")
    payment_transaction_id = fields.Many2one('payment.transaction', string="Payment Transaction")

    @api.model
    def create_reservation_from_sale_order(self, sale_order):
        """Create hotel reservations from a confirmed sale order containing rooms."""
        for line in sale_order.order_line.filtered(lambda l: l.room_id):
            checkin = line.checkin_date if hasattr(line, 'checkin_date') else fields.Date.today()
            checkout = line.checkout_date if hasattr(line, 'checkout_date') else checkin + timedelta(days=1)

            # Check if room is available
            if not line.room_id.is_available(checkin, checkout, line.product_uom_qty):
                _logger.warning('Room %s not available for SO %s', line.room_id.name, sale_order.name)
                continue

            # Create the booking
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
            self.create(booking_vals)
        return True

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