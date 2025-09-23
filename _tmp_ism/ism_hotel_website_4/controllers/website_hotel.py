# odoo_hotel_cart_integration.py
# Controller + Model extensions for hotel bookings into Odoo website cart
# Drop-in ready

import logging
import re
from datetime import datetime, timedelta

from odoo import http, fields, models, api, _
from odoo.http import request

_logger = logging.getLogger(__name__)


# --------------------------
# Helpers
# --------------------------
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




# --------------------------
# Controller
# --------------------------
class WebsiteIsmHotel(http.Controller):

    @http.route(['/hotel', '/hotel/rooms'], type='http', auth='public', website=True, sitemap=True)
    def hotel_list(self, checkin=None, checkout=None, guests=2, category_id=None, **kw):
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
            except Exception:
                available = False

            try:
                rate = r.get_rate_for_dates(checkin_date, checkout_date)
            except Exception:
                rate = r.base_price or (r.room_type and r.room_type.list_price) or 0.0

            cards.append({"room": r, "available": available, "rate": rate})

        categories = request.env['product.category'].sudo().search([])

        return request.render('ism_hotel_website_4.website_hotel_home', {
            'cards': cards,
            'checkin': checkin,
            'checkout': checkout,
            'guests': guests,
            'checkin_min': fields.Date.to_string(today),
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

    @http.route(['/hotel/room/<int:room_id>/book'], type='http', auth='public',
                website=True, methods=['GET', 'POST'], csrf=True)
    def hotel_booking_checkout(self, room_id, **post):
        room = request.env['hotel.room'].sudo().browse(room_id)
        if not room.exists():
            return request.not_found()

        def _render_checkout(ctx_extra=None):
            checkin = post.get('checkin') or fields.Date.to_string(fields.Date.context_today(request.env.user))
            checkout = post.get('checkout') or fields.Date.to_string(fields.Date.from_string(checkin) + timedelta(days=1))
            guests = int(post.get('guests') or 2)
            checkin_date = _parse_date(checkin)
            checkout_date = _parse_date(checkout)
            nights = max(1, (checkout_date - checkin_date).days)

            rate = room.get_rate_for_dates(checkin_date, checkout_date) if hasattr(room, 'get_rate_for_dates') else \
                (room.base_price or (room.room_type and room.room_type.list_price) or 0.0)
            subtotal = nights * (rate or 0.0)

            base_ctx = {
                'room': room,
                'checkin': checkin,
                'checkout': checkout,
                'guests': guests,
                'rate': rate,
                'nights': nights,
                'subtotal': subtotal,
                'total': subtotal,  # Taxes will be added in Odoo checkout
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

        # --------------------------
        # POST = Add to cart
        # --------------------------
        if request.httprequest.method == 'POST':
            errors = {}

            # validations
            if not post.get('name') or len(post.get('name').strip()) < 2:
                errors['name'] = _('Please enter a valid full name.')
            email = post.get('email', '').strip()
            if not email or not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
                errors['email'] = _('Please enter a valid email address.')
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
            max_allowed = getattr(room, 'max_allowed_person', None) or getattr(room, 'max_guests', None)
            if max_allowed and guests > max_allowed:
                errors['guests'] = _('Selected room cannot accommodate that many guests.')

            if not errors and not room.is_available(checkin, checkout, guests=guests):
                errors['availability'] = _('Room not available for selected dates.')

            if errors:
                return _render_checkout({'errors': errors})

            # pricing
            nights = max(1, (checkout - checkin).days)
            rate = room.get_rate_for_dates(checkin, checkout) if hasattr(room, 'get_rate_for_dates') else (room.base_price or (room.room_type and room.room_type.list_price) or 0.0)
            subtotal = nights * (rate or 0.0)

            # ensure order
            order = request.website.sale_get_order(force_create=True)
            
            # Clear existing cart lines before adding new booking to ensure only one product
            if order and order.order_line:
                for line in order.order_line:
                    line.sudo().unlink()
                _logger.info('Cleared existing cart lines before adding new hotel booking')

            # create SOL with forced price and custom name
            sol_vals = {
                'order_id': order.id,
                'product_id': room.room_type.id,
                'name': f"{room.name} ({checkin} to {checkout})",  # Custom name for booking
                'product_uom_qty': 1,
                'price_unit': subtotal,
                'room_id': room.id,
                'checkin': checkin,
                'checkout': checkout,
                'guests': guests,
                'special_requests': post.get('special_requests'),
                'is_hotel_booking': True,  # Mark as hotel booking to preserve custom price
            }
            _logger.info('Creating sale.order.line with values: %s', sol_vals)
            try:
                # Create with multiple context flags to force price
                sol = request.env['sale.order.line'].with_context(
                    force_price=True,
                    skip_pricelist=True,
                    pricelist_browse=False
                ).sudo().create(sol_vals)
                
                # Force the price again after creation
                sol.sudo().write({'price_unit': subtotal})
                _logger.info('Created SOL with product %s, forced price_unit: %s', room.room_type.id, sol.price_unit)
                
                # Create draft booking immediately after SOL creation
                Book = request.env['hotel.book.history'].sudo()
                booking_vals = {
                    'partner_id': partner.id,
                    'room_id': room.id,
                    'check_in': checkin,
                    'check_out': checkout,
                    'name': f'Website Booking - {room.name}',
                    'rate': rate,
                    'guests': guests,
                    'email': partner.email,
                    'phone': partner.phone,
                    'special_requests': post.get('special_requests'),
                    'state': 'draft',
                }
                booking = Book.create(booking_vals)
                _logger.info('Draft booking %s created for partner %s', booking.id, partner.name)
                
            except Exception as e:
                _logger.exception('Failed to create sale.order.line for room cart: %s', e)
                return _render_checkout({'errors': {'cart': _('Could not add item to cart.')}})

            # Check if payment providers are available
            providers = request.env['payment.provider'].sudo().search([('state', '=', 'enabled')])
            if providers:
                # Create payment transaction and redirect to payment
                return self._create_payment_transaction(room, partner, checkin, checkout, guests, rate, nights, post.get('special_requests'))
            else:
                # Fallback to cart checkout
                return request.redirect('/shop/checkout')

        # --------------------------
        # GET = preview
        # --------------------------
        return _render_checkout()

    def _create_payment_transaction(self, room, partner, checkin, checkout, guests, rate, nights, special_requests):
        """Create payment transaction and redirect to payment provider"""
        try:
            # Prefer demo provider if available
            provider = request.env['payment.provider'].sudo().search([
                ('state', '=', 'enabled'), 
                ('code', '=', 'demo')
            ], limit=1)
            
            if not provider:
                provider = request.env['payment.provider'].sudo().search([
                    ('state', '=', 'enabled')
                ], limit=1)
            
            if not provider:
                _logger.warning('No enabled payment provider found')
                return request.redirect('/shop/checkout')

            # Calculate total amount
            subtotal = nights * rate
            currency = request.env.company.currency_id
            
            # Create payment transaction
            reference = request.env['payment.transaction']._generate_reference('hotel_booking')
            tx = request.env['payment.transaction'].sudo().create({
                'amount': subtotal,
                'currency_id': currency.id,
                'partner_id': partner.id,
                'provider_id': provider.id,
                'reference': reference,
                'state': 'draft',
            })

            # Create a draft booking to link with payment
            Book = request.env['hotel.book.history'].sudo()
            booking_vals = {
                'partner_id': partner.id,
                'room_id': room.id,
                'check_in': checkin,
                'check_out': checkout,
                'name': f'Hotel Booking - {room.name}',
                'rate': rate,
                'guests': guests,
                'email': partner.email,
                'phone': partner.phone,
                'special_requests': special_requests,
                'payment_transaction_id': tx.id,
                'payment_reference': reference,
                'payment_provider_id': provider.id,
                'payment_status': 'pending',
                'state': 'draft',
            }
            
            booking = Book.create(booking_vals)
            _logger.info('Created draft booking %s for payment transaction %s', booking.id, reference)

            # Get checkout URL from provider
            checkout_url = tx.get_checkout_url()
            if checkout_url:
                _logger.info('Redirecting to payment checkout: %s', checkout_url)
                return request.redirect(checkout_url)
            else:
                # Fallback to manual payment form
                return request.render('ism_hotel_website_4.website_hotel_payment_form', {
                    'tx': tx,
                    'room': room,
                    'checkin': checkin,
                    'checkout': checkout,
                    'guests': guests,
                    'nights': nights,
                    'subtotal': subtotal,
                    'provider': provider,
                })

        except Exception as e:
            _logger.exception('Failed to create payment transaction: %s', e)
            return request.redirect('/shop/checkout')

    @http.route(['/hotel/payment/confirm/<string:reference>'], type='http', auth='public', website=True)
    def payment_confirm(self, reference, **post):
        """Handle payment confirmation callback"""
        tx = request.env['payment.transaction'].sudo().search([('reference', '=', reference)], limit=1)
        if not tx:
            return request.not_found()

        if tx.state == 'done':
            # Payment successful - create booking
            return self._create_booking_from_transaction(tx)
        else:
            # Payment failed
            return request.render('ism_hotel_website_4.website_hotel_payment_failed', {
                'tx': tx,
                'error': 'Payment was not successful'
            })

    def _create_booking_from_transaction(self, tx):
        """Create hotel booking from successful payment transaction"""
        try:
            # Look for existing booking with this transaction reference
            Book = request.env['hotel.book.history'].sudo()
            existing_booking = Book.search([('payment_reference', '=', tx.reference)], limit=1)
            
            if existing_booking:
                # Update existing booking with payment info
                existing_booking.sudo().write({
                    'payment_transaction_id': tx.id,
                    'payment_status': 'paid',
                    'payment_provider_id': tx.provider_id.id,
                    'state': 'booked',
                })
                booking = existing_booking
            else:
                # Create new booking from transaction
                booking_vals = {
                    'partner_id': tx.partner_id.id,
                    'name': f'Payment Booking - {tx.reference}',
                    'rate': tx.amount,
                    'state': 'booked',
                    'email': tx.partner_id.email,
                    'phone': tx.partner_id.phone,
                    'payment_transaction_id': tx.id,
                    'payment_status': 'paid',
                    'payment_reference': tx.reference,
                    'payment_provider_id': tx.provider_id.id,
                }
                
                booking = Book.create(booking_vals)
                booking.sudo().action_confirm()
            
            return request.render('ism_hotel_website_4.website_hotel_payment_success', {
                'tx': tx,
                'booking': booking,
            })
            
        except Exception as e:
            _logger.exception('Failed to create booking from transaction: %s', e)
            return request.render('ism_hotel_website_4.website_hotel_payment_failed', {
                'tx': tx,
                'error': 'Booking creation failed'
            })

    @http.route(['/hotel/payment/providers'], type='http', auth='public', website=True)
    def payment_providers(self, **kw):
        """Show available payment providers"""
        providers = request.env['payment.provider'].sudo().search([('state', '=', 'enabled')])
        return request.render('ism_hotel_website_4.website_hotel_payment_providers', {
            'providers': providers,
        })
