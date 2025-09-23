import logging
import re
from datetime import datetime, timedelta

from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)

def _get_partner_from_request(post):
    uid = request.env.user.id if request.env.user else False
    public_id = request.env.ref('base.public_user').id
    partner = request.env.user.partner_id if uid and uid != public_id else None
    if not partner:
        partner = request.env['res.partner'].sudo().create({
            'name': post.get('name') or _('Website Guest'),
            'email': post.get('email'),
            'phone': post.get('phone'),
        })
    return partner

def _parse_date(dstr):
    if not dstr:
        return None
    try:
        return datetime.strptime(dstr, '%Y-%m-%d').date()
    except Exception:
        return None

class WebsiteIsmHotel(http.Controller):

    @http.route(['/hotel', '/hotel/rooms'], type='http', auth='public', website=True, sitemap=True)
    def hotel_list(self, checkin=None, checkout=None, guests=2, category_id=None, **kw):
        # allow browsing without login for discovery
        checkin = kw.get('checkin') or checkin
        checkout = kw.get('checkout') or checkout
        guests = int(kw.get('guests') or guests or 2)
        category_id = int(kw.get('category_id') or category_id or 0)

        today = fields.Date.context_today(request.env.user or request.env['res.users'].sudo().browse(request.uid))
        if not checkin:
            checkin = fields.Date.to_string(today)
        if not checkout:
            checkout = fields.Date.to_string(fields.Date.from_string(checkin) + timedelta(days=1))

        checkin_date = _parse_date(checkin)
        checkout_date = _parse_date(checkout)

        Room = request.env['hotel.room'].sudo()
        domain = [('is_published', '=', True)]
        if category_id:
            domain.append(('website_category_id', '=', category_id))
        rooms = Room.search(domain)

        cards = []
        for r in rooms:
            try:
                available = r.is_available(checkin_date, checkout_date, guests=guests)
            except Exception as e:
                _logger.exception('Availability check failed for room %s: %s', r.id, e)
                available = False

            try:
                rate = r.get_rate_for_dates(checkin_date, checkout_date)
            except Exception:
                rate = r.base_price or (r.room_type and r.room_type.list_price) or 0.0

            if available:
                cards.append({"room": r, "available": available, "rate": rate})

        checkin_min = fields.Date.to_string(today)

        categories = request.env['product.category'].sudo().search([])

        return request.render('ism_hotel_website_4.website_hotel_home', {
            'cards': cards,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'checkin_min': checkin_min,
            'categories': categories,
            'category_id': category_id,
        })

    @http.route(['/hotel/room/<int:room_id>'], type='http', auth='public', website=True, sitemap=True)
    def hotel_room_detail(self, room_id, **kw):
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.not_found()
        product = getattr(room, 'room_type', None)
        return request.render('ism_hotel_website_4.website_hotel_room_detail', {
            'room': room,
            'product': product,
        })

    @http.route(['/hotel/room/<int:room_id>/book'], type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=True)
    def hotel_booking_checkout(self, room_id, **post):
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.not_found()

        def _render_checkout(ctx_extra=None):
            # rebuild preview
            checkin = post.get('checkin') or fields.Date.to_string(fields.Date.context_today(request.env.user))
            checkout = post.get('checkout') or fields.Date.to_string(fields.Date.from_string(checkin) + timedelta(days=1))
            guests = int(post.get('guests') or 2)
            checkin_date = _parse_date(checkin)
            checkout_date = _parse_date(checkout)
            nights = max(1, (checkout_date - checkin_date).days)

            rate = room.get_rate_for_dates(checkin_date, checkout_date) if hasattr(room, 'get_rate_for_dates') else (room.base_price or (room.room_type and room.room_type.list_price) or 0.0)
            subtotal = nights * (rate or 0.0)

            # discount logic for preview
            pay_now_discount = 135.0 if subtotal >= 6000 else 0.0
            tax_percent = getattr(room, 'tax_percent', 12.0) or 0.0
            tax = max(subtotal - pay_now_discount, 0.0) * tax_percent / 100.0
            total = max(subtotal - pay_now_discount, 0.0) + tax

            base_ctx = {
                'room': room,
                'checkin': checkin,
                'checkout': checkout,
                'guests': guests,
                'rate': rate,
                'nights': nights,
                'subtotal': subtotal,
                'pay_now_discount': pay_now_discount,
                'tax': tax,
                'total': total,
                'checkin_min': fields.Date.to_string(fields.Date.context_today(request.env.user)),
                'errors': {},
                'values': {
                    'name': post.get('name', ''),
                    'email': post.get('email', ''),
                    'phone': post.get('phone', ''),
                    'special_requests': post.get('special_requests', ''),
                }
            }
            if ctx_extra:
                base_ctx.update(ctx_extra)
            return request.render('ism_hotel_website_4.website_hotel_booking_checkout', base_ctx)

        if request.httprequest.method == 'POST':
            errors = {}

            # 1. Name
            if not post.get('name') or len(post.get('name').strip()) < 2:
                errors['name'] = _('Please enter a valid full name.')

            # 2. Email
            email = post.get('email', '').strip()
            email_pattern = r"^[^@]+@[^@]+\.[^@]+$"
            if not email or not re.match(email_pattern, email):
                errors['email'] = _('Please enter a valid email address.')

            # 3. Phone
            phone = post.get('phone', '').strip()
            if not phone.isdigit() or len(phone) < 7:
                errors['phone'] = _('Please enter a valid phone number.')

            partner = _get_partner_from_request(post)

            checkin = _parse_date(post.get('checkin'))
            checkout = _parse_date(post.get('checkout'))
            if not checkin or not checkout:
                errors['date'] = _('Invalid date format.')

            today = fields.Date.context_today(request.env.user)
            if checkin and checkin < today:
                errors['checkin'] = _('Past dates are not allowed.')
            if checkin and checkout and checkout <= checkin:
                errors['checkout'] = _('Check-out must be after check-in.')

            guests = int(post.get('guests') or 2)

            # Capacity validation
            max_allowed = getattr(room, 'max_allowed_person', None) or getattr(room, 'max_guests', None)
            if max_allowed and guests > max_allowed:
                errors['guests'] = _('Selected room cannot accommodate that many guests.')

            # Availability (with guests)
            if not errors and not room.is_available(checkin, checkout, guests=guests):
                errors['availability'] = _('Room not available for selected dates.')

            if errors:
                return _render_checkout({'errors': errors})

            # Compute rate/amounts for persistence
            rate = room.get_rate_for_dates(checkin, checkout) if hasattr(room, 'get_rate_for_dates') else (room.base_price or (room.room_type and room.room_type.list_price) or 0.0)
            nights = max(1, (checkout - checkin).days)
            subtotal = nights * (rate or 0.0)
            discount_amount = 135.0 if subtotal >= 6000 else 0.0

            Book = request.env['hotel.book.history'].sudo()
            vals = {
                'partner_id': partner.id,
                'check_in': checkin,
                'check_out': checkout,
                'room_id': room.id,  # IMPORTANT: correct schema
                'name': _('Website Booking'),
                'rate': rate,
                'discount_amount': discount_amount,
                'guests': guests,
                'email': post.get('email'),
                'phone': post.get('phone'),
                'special_requests': post.get('special_requests'),
            }
            booking = Book.create(vals)
            booking.sudo().action_confirm()

            return request.redirect('/hotel/booking/thanks/%s' % booking.id)

        # GET -> preview
        return _render_checkout()

    @http.route(['/hotel/booking/thanks/<int:booking_id>'], type='http', auth='public', website=True)
    def booking_thanks(self, booking_id, **kw):
        booking = request.env['hotel.book.history'].sudo().browse(booking_id)
        if not booking.exists():
            return request.not_found()
        # show enabled payment providers after booking
        providers = request.env['payment.provider'].sudo().search([('state', '=', 'enabled')])
        return request.render('ism_hotel_website_4.website_hotel_booking_thanks', {
            'booking': booking,
            'providers': providers,
        })
