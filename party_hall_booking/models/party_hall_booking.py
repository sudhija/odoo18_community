from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, time
import pytz

class PartyHallBooking(models.Model):
    _name = 'party.hall.booking'
    _description = 'Party Hall Booking'

    hall_id = fields.Many2one('party.hall', string='Hall', required=True)
    booking_date = fields.Date(string='Booking Date', required=True)
    slot = fields.Selection([
        ('morning', 'Morning (9:00 AM - 3:00 PM)'),
        ('evening', 'Evening (4:00 PM - 9:00 PM)'),
        ('full_day', 'Full Day (9:00 AM - 9:00 PM)'),
    ], string='Slot', required=True)
    customer_name = fields.Char(string='Customer Name', required=True)
    customer_email = fields.Char(string='Customer Email')
    customer_phone = fields.Char(string='Customer Phone')
    notes = fields.Text(string='Notes')
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled')
    ], default='pending', string='Status')

    @api.constrains('hall_id', 'booking_date', 'slot', 'state')
    def _check_slot_restrictions(self):
        for rec in self:
            if rec.state == 'cancelled':
                continue  # Skip cancelled bookings

            if not rec.booking_date or not rec.slot:
                continue

            user_tz = self.env.user.tz or 'Asia/Kolkata'
            now = datetime.now(pytz.timezone(user_tz))
            today = now.date()
            now_time = now.time()

            # Prevent booking for past dates
            if rec.booking_date < today:
                raise ValidationError("You cannot book for a past date.")

            # Time-based restrictions for today
            if rec.booking_date == today:
                if now_time >= time(21, 0):  # After 9 PM
                    raise ValidationError("You cannot book any slot after 9 PM today.")
                if now_time >= time(15, 0) and rec.slot != 'evening':
                    raise ValidationError("After 3 PM, only the Evening slot is allowed for today.")
                if now_time < time(15, 0) and rec.slot != 'morning':
                    raise ValidationError("Before 3 PM, only the Morning slot is allowed for today.")

            # Check slot conflicts (ignore cancelled bookings)
            domain = [
                ('id', '!=', rec.id),
                ('hall_id', '=', rec.hall_id.id),
                ('booking_date', '=', rec.booking_date),
                ('state', '!=', 'cancelled'),  # ignore cancelled bookings
            ]
            existing_bookings = self.search(domain)
            existing_slots = [b.slot for b in existing_bookings]

            if rec.slot == 'morning' and ('morning' in existing_slots or 'full_day' in existing_slots):
                raise ValidationError("Morning slot is already booked or Full Day booking exists.")
            if rec.slot == 'evening' and ('evening' in existing_slots or 'full_day' in existing_slots):
                raise ValidationError("Evening slot is already booked or Full Day booking exists.")
            if rec.slot == 'full_day' and existing_bookings:
                raise ValidationError("Full Day slot cannot be booked because another slot is already booked.")
