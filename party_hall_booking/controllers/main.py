from odoo import http, fields
from odoo.http import request
from datetime import datetime, time
import pytz

class PartyHallWebsite(http.Controller):

    @http.route(['/party_halls'], type='http', auth='public', website=True)
    def list_page(self, **kw):
        halls = request.env['party.hall'].sudo().search([], order="is_recommended desc, name asc")
        return request.render('party_hall_booking.list_template', {'halls': halls})

    @http.route(['/party_hall/<model("party.hall"):hall>'], type='http', auth='public', website=True)
    def detail_page(self, hall, **kw):
        today = fields.Date.today()  # returns 'YYYY-MM-DD' string
        return request.render('party_hall_booking.detail_template', {
            'hall': hall,
            'today': today,
            'prefill': kw
        })
    @http.route(['/catering-service'], type='http', auth="public", website=True) 
    def catering_service_page(self, **kwargs):
        return request.render('website_catering_service.catering_page_template')
        
    @http.route(['/check_availability'], type='http', auth='public', website=True, methods=['POST'])
    def check_availability(self, **post):
        hall_id = int(post.get('hall_id'))
        date = post.get('booking_date')
        slot = post.get('slot')
        hall = request.env['party.hall'].sudo().browse(hall_id)
        if not hall or not date or not slot:
            return request.render('party_hall_booking.detail_template', {
                'hall': hall,
                'availability_message': "Please select date and slot.",
                'prefill': post
            })

        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        today = now.date()
        now_time = now.time()

        # Time-based Restrictions for Today
        if booking_date == today:
            if now_time >= time(21, 0):
                # After 9 PM
                return request.render('party_hall_booking.detail_template', {
                    'hall': hall,
                    'availability_message': "You cannot book any slot after 9 PM today.",
                    'prefill': post
                })
            if now_time >= time(15, 0):
                # After 3 PM
                if slot != 'evening':
                    return request.render('party_hall_booking.detail_template', {
                        'hall': hall,
                        'availability_message': "After 3 PM, only Evening slot is allowed for today.",
                        'prefill': post
                    })
            if now_time < time(15, 0):
                # Before 3 PM
                if slot != 'morning':
                    return request.render('party_hall_booking.detail_template', {
                        'hall': hall,
                        'availability_message': "Before 3 PM, only Morning slot is allowed for today.",
                        'prefill': post
                    })

         # ✅ Check if slot is already booked (ignore cancelled bookings)
        existing_bookings = request.env['party.hall.booking'].sudo().search([
            ('hall_id', '=', hall_id),
            ('booking_date', '=', booking_date),
            ('state', '!=', 'cancelled')  # Ignore cancelled bookings
        ])
        if slot == 'morning' and any(b.slot in ['morning', 'full_day'] for b in existing_bookings):
            return request.render('party_hall_booking.detail_template', {
                'hall': hall,
                'availability_message': "Morning slot is already booked or Full Day booking exists.",
                'prefill': post
            })
        if slot == 'evening' and any(b.slot in ['evening', 'full_day'] for b in existing_bookings):
            return request.render('party_hall_booking.detail_template', {
                'hall': hall,
                'availability_message': "Evening slot is already booked or Full Day booking exists.",
                'prefill': post
            })
        if slot == 'full_day' and existing_bookings:
            return request.render('party_hall_booking.detail_template', {
                'hall': hall,
                'availability_message': "Full Day slot cannot be booked because another slot is already booked.",
                'prefill': post
            })

        return request.render('party_hall_booking.detail_template', {
            'hall': hall,
            'availability_message': "Slot is available! You can proceed with booking.",
            'availability_success': True,
            'prefill': post
        })

    @http.route(['/booking_submit'], type='http', auth='public', website=True, methods=['POST'])
    def booking_submit(self, **post):
        hall_id = int(post.get('hall_id'))
        date = post.get('booking_date')
        slot = post.get('slot')
        name = post.get('customer_name')
        phone = post.get('customer_phone')
        hall = request.env['party.hall'].sudo().browse(hall_id)
        booking_date = datetime.strptime(date, "%Y-%m-%d").date()
        now = datetime.now(pytz.timezone('Asia/Kolkata'))
        today = now.date()
        now_time = now.time()
         # ❌ Past date check
        if booking_date < today:
            return request.render('party_hall_booking.failed_template', {
                'error': 'You cannot book for a past date.'
            })

        # Time-based Restrictions for Today
        if booking_date == today:
            if now_time >= time(21, 0):
                return request.render('party_hall_booking.failed_template', {
                    'error': 'You cannot book any slot after 9 PM today.'
                })
            if now_time >= time(15, 0):
                if slot != 'evening':
                    return request.render('party_hall_booking.failed_template', {
                        'error': 'After 3 PM, only Evening slot is allowed for today.'
                    })
            if now_time < time(15, 0):
                if slot != 'morning':
                    return request.render('party_hall_booking.failed_template', {
                        'error': 'Before 3 PM, only Morning slot is allowed for today.'
                    })

        # ✅ Check if slot is already booked (ignore cancelled bookings)
        existing_bookings = request.env['party.hall.booking'].sudo().search([
            ('hall_id', '=', hall_id),
            ('booking_date', '=', booking_date),
            ('state', '!=', 'cancelled')  # Ignore cancelled bookings
        ])
        if slot == 'morning' and any(b.slot in ['morning', 'full_day'] for b in existing_bookings):
            return request.render('party_hall_booking.failed_template', {
                'error': 'Morning slot is already booked or Full Day booking exists.'
            })
        if slot == 'evening' and any(b.slot in ['evening', 'full_day'] for b in existing_bookings):
            return request.render('party_hall_booking.failed_template', {
                'error': 'Evening slot is already booked or Full Day booking exists.'
            })
        if slot == 'full_day' and existing_bookings:
            return request.render('party_hall_booking.failed_template', {
                'error': 'Full Day slot cannot be booked because another slot is already booked.'
            })

        # Create booking
        request.env['party.hall.booking'].sudo().create({
            'hall_id': hall_id,
            'booking_date': booking_date,
            'slot': slot,
            'customer_name': name,
            'customer_phone': phone,
        })

        return request.render('party_hall_booking.thanks_template', {
            'name': name,
            'hall': hall,
            'date': date,
            'slot': slot
        })
    
