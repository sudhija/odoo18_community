import re
from odoo import http
from odoo.http import request
from datetime import datetime

class PartyHallWebsite(http.Controller):

    @http.route(['/party_hall/booking/submit'], type='http', auth='public', methods=['POST'], website=True, csrf=True)
    def booking_submit(self, **post):
        hall_id = post.get('hall_id')
        booking_date = post.get('booking_date')
        slot = post.get('slot')
        customer_name = post.get('customer_name')
        customer_email = post.get('customer_email')
        customer_phone = post.get('customer_phone')
        notes = post.get('notes')

        # --- Mandatory Fields ---
        if not (hall_id and booking_date and slot and customer_name and customer_phone):
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'Please fill all mandatory fields.'}
            )

        # --- Full Name Validation (Alphabets only) ---
        if not re.fullmatch(r"[A-Za-z ]+", customer_name.strip()):
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'Full Name can contain only alphabets.'}
            )

        # --- Phone Validation (10 digits only) ---
        if not re.fullmatch(r"\d{10}", customer_phone.strip()):
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'Phone number must be exactly 10 digits.'}
            )

        # --- Optional Email: if provided, check format ---
        if customer_email:
            if not re.fullmatch(r"[^@]+@[^@]+\.[^@]+", customer_email.strip()):
                return request.render(
                    'party_hall_booking.failed_template',
                    {'error': 'Invalid email address.'}
                )

        # --- Date Validation ---
        today = datetime.today().date()
        try:
            booking_dt = datetime.strptime(booking_date, "%Y-%m-%d").date()
        except Exception:
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'Invalid date format.'}
            )

        if booking_dt < today:
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'You cannot book for a past date.'}
            )

        # --- Prevent duplicate bookings ---
        dup = request.env['party.hall.booking'].sudo().search_count([
            ('hall_id', '=', int(hall_id)),
            ('booking_date', '=', booking_date),
            ('slot', '=', slot),
        ])
        if dup:
            return request.render(
                'party_hall_booking.failed_template',
                {'error': 'Selected slot already booked. Please choose another.'}
            )

        # --- Create booking ---
        vals = {
            'hall_id': int(hall_id),
            'booking_date': booking_date,
            'slot': slot,
            'customer_name': customer_name,
            'customer_email': customer_email,
            'customer_phone': customer_phone,
            'notes': notes,
        }
        request.env['party.hall.booking'].sudo().create(vals)
        return request.redirect('/party_hall/booking/thanks')
