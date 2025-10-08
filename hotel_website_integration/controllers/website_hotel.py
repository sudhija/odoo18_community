import logging
import re
from datetime import datetime, timedelta, date
from odoo import http, fields, models, _
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

def _dates_overlap(line_checkin_dt, line_checkout_dt, req_checkin_d, req_checkout_d):
    # Convert datetimes to dates for comparison
    if isinstance(line_checkin_dt, datetime):
        line_checkin_d = line_checkin_dt.date()
    else:
        line_checkin_d = line_checkin_dt
    if isinstance(line_checkout_dt, datetime):
        line_checkout_d = line_checkout_dt.date()
    else:
        line_checkout_d = line_checkout_dt
    return (line_checkin_d <= req_checkout_d) and (line_checkout_d >= req_checkin_d)

def _is_room_available(room, checkin_d: date, checkout_d: date, guests=1):
    # Consider bookings in reserved/check_in as blocking
    Line = request.env['room.booking.line'].sudo()
    lines = Line.search([
        ('room_id', '=', room.id),
        ('booking_id.state', 'in', ['reserved', 'check_in']),
    ])
    for l in lines:
        if _dates_overlap(l.checkin_date, l.checkout_date, checkin_d, checkout_d):
            return False
    max_allowed = getattr(room, 'max_allowed_person', None) or getattr(room, 'max_guests', None)
    if max_allowed and guests and guests > max_allowed:
        return False
    return True

def _get_rate_for_dates(room, checkin_d: date, checkout_d: date):
    # Try room-specific pricing if present, else fallback to list_price
    try:
        if hasattr(room, 'get_rate_for_dates'):
            return room.get_rate_for_dates(checkin_d, checkout_d)
    except Exception:
        pass
    # Try room_type pricing or own list_price
    base = 0.0
    try:
        base = room.base_price
    except Exception:
        base = 0.0
    if not base:
        try:
            base = (room.room_type and room.room_type.list_price) or 0.0
        except Exception:
            base = 0.0
    if not base:
        try:
            base = room.list_price
        except Exception:
            base = 0.0
    return base or 0.0

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
            available = _is_room_available(r, checkin_date, checkout_date, guests=guests)
            rate = _get_rate_for_dates(r, checkin_date, checkout_date)
            cards.append({"room": r, "available": available, "rate": rate})

        categories = request.env['product.category'].sudo().search([])

        return request.render('hotel_website_integration.website_hotel_home', {
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
        return request.render('hotel_website_integration.website_hotel_room_detail', {
            'room': room,
            'product': product,
        })


    @http.route(['/hotel/room/<int:room_id>/book'], type='http', auth='public', website=True, methods=['GET', 'POST'], csrf=True)
    def hotel_booking_checkout(self, room_id, **post):
        """
        Streamlined: Only add-to-cart flow, improved error handling, and session management.
        """
        errors = {}
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
            rate = _get_rate_for_dates(room, checkin_date, checkout_date)
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
            return request.render('hotel_website_integration.website_hotel_booking_checkout', base_ctx)

        if request.httprequest.method == 'POST':
            # Improved error handling and user feedback
            try:
                if not post.get('name') or len(post.get('name').strip()) < 2:
                    errors['name'] = _('Please enter a valid full name.')
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
                if not _is_room_available(room, checkin, checkout, guests=guests):
                    errors['availability'] = _('Room not available for selected dates.')
                if errors:
                    _logger.info('Hotel checkout validation errors for room %s: %s', room.id, errors)
                    return _render_checkout({'errors': errors})
                nights = max(1, (checkout - checkin).days)
                rate = _get_rate_for_dates(room, checkin, checkout)
                subtotal = nights * (rate or 0.0)
                order = request.website.sale_get_order(force_create=True)
                if not order:
                    _logger.error('Could not create or fetch sale order for booking.')
                    return _render_checkout({'errors': {'cart': _('Could not create a shopping cart. Please try again later.')}})
                if order and partner:
                    order.sudo().write({'partner_id': partner.id})
                # Remove previous cart lines for a clean booking
                if order and order.order_line:
                    for line in order.order_line:
                        line.sudo().unlink()
                product_variant = getattr(room, 'product_id', None)
                if product_variant and getattr(product_variant, '_name', '') == 'product.template':
                    pv = product_variant.product_variant_ids[:1]
                    product_variant = pv and pv[0] or None
                if not product_variant or getattr(product_variant, '_name', '') != 'product.product':
                    _logger.error('Room product is not configured for website sale: room_id=%s', room.id)
                    return _render_checkout({'errors': {'cart': _('Room product is not configured for website sale.')}})
                sol_vals = {
                    'order_id': order.id,
                    'product_id': product_variant.id,
                    'name': f"{room.name} ({checkin} → {checkout})",
                    'product_uom_qty': 1,
                    'product_uom': (getattr(product_variant, 'uom_id', False) and getattr(product_variant.uom_id, 'id', False)) or request.env.ref('uom.product_uom_unit').id,
                    'price_unit': subtotal,
                    'room_id': room.id,
                    'checkin': checkin,
                    'checkout': checkout,
                    'guests': guests,
                    'special_requests': post.get('special_requests'),
                }
                try:
                    sol = request.env['sale.order.line'].with_context(
                        force_price=True,
                        skip_pricelist=True,
                        pricelist_browse=False,
                        website_id=request.website.id,
                    ).sudo().create(sol_vals)
                    request.env['hotel.room'].fix_website_flags()#####
                    sol.sudo().write({'price_unit': subtotal, 'product_uom_qty': 1})
                    _logger.info('Created cart line for room booking: SOL %s', sol.id)
                except Exception as e:
                    _logger.exception('Failed to create sale order line: %s', e)
                    return _render_checkout({'errors': {'cart': _('Could not add item to cart. Please contact support if this persists.')}})
                request.session['sale_order_id'] = order.id
                request.session['sale_last_order_id'] = order.id
                request.env['hotel.room'].fix_website_flags()#####
                _logger.info('Set sale_order_id and sale_last_order_id in session: %s', order.id)
                return request.redirect('/shop/checkout')
            except Exception as e:
                import traceback
                _logger.exception('Unexpected error in hotel booking checkout: %s', e)
                return _render_checkout({'errors': {'cart': _('An unexpected error occurred. Please try again or contact support.')}})
        return _render_checkout()

    @http.route(['/hotel/reservation/confirm/<int:reservation_id>'], type='http', auth='user', website=True)
    def hotel_reservation_confirm(self, reservation_id, **kw):
        reservation = request.env['hotel.reservation'].sudo().browse(reservation_id)
        if not reservation.exists() or reservation.partner_id.id != request.env.user.partner_id.id:
            return request.not_found()
        return request.render('hotel_website_integration.website_hotel_booking_thanks', {'reservation': reservation})

    @http.route(['/hotel/reservation/status/<string:reference>'], type='http', auth='public', website=True)
    def hotel_reservation_status(self, reference, **kw):
        reservation = request.env['hotel.reservation'].sudo().search([('name', '=', reference)], limit=1)
        if not reservation:
            return request.render('hotel_website_integration.website_hotel_payment_failed', {'error': 'Reservation not found.'})
        return request.render('hotel_website_integration.website_hotel_booking_thanks', {'reservation': reservation})

    @http.route(['/hotel/reservation/error'], type='http', auth='public', website=True)
    def hotel_reservation_error(self, **kw):
        return request.render('hotel_website_integration.website_hotel_payment_failed', {'error': 'There was a problem with your booking. Please try again or contact support.'})

    def _create_payment_transaction(self, room, partner, checkin, checkout, guests, rate, nights, special_requests):
        """Create payment transaction and redirect to payment provider"""
        try:
            provider = request.env['payment.provider'].sudo().search([
                ('state', 'in', ['enabled', 'test']),
                ('code', '=', 'demo')
            ], limit=1)
            if not provider:
                provider = request.env['payment.provider'].sudo().search([
                    ('state', 'in', ['enabled', 'test'])
                ], limit=1)
            if not provider:
                _logger.warning('No enabled payment provider found')
                return request.redirect('/shop/checkout')

            subtotal = nights * rate
            currency = request.env.company.currency_id

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
            try:
                Book = request.env['room.booking'].sudo()
                booking_vals = {
                    'partner_id': partner.id,
                    'checkin_date': fields.Datetime.to_datetime(str(checkin)),
                    'checkout_date': fields.Datetime.to_datetime(str(checkout)),
                    'need_food': False,
                    'need_service': False,
                    'need_fleet': False,
                    'need_event': False,
                }
                booking = Book.create(booking_vals)
                
                # Create booking line
                request.env['room.booking.line'].sudo().create({
                    'booking_id': booking.id,
                    'room_id': room.id,
                    'checkin_date': fields.Datetime.to_datetime(str(checkin)),
                    'checkout_date': fields.Datetime.to_datetime(str(checkout)),
                    'uom_qty': nights,
                })
                
                _logger.info('Created draft booking %s for payment transaction %s', booking.id, reference)
            except Exception as e:
                _logger.warning('Could not create draft booking: %s', e)

            # Get checkout URL from provider
            try:
                checkout_url = tx.get_checkout_url()
                if checkout_url:
                    _logger.info('Redirecting to payment checkout: %s', checkout_url)
                    return request.redirect(checkout_url)
            except Exception as e:
                _logger.warning('Could not get checkout URL: %s', e)
            
            # Fallback to manual payment form
            return request.render('hotel_website_integration.website_hotel_payment_form', {
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
            return self._create_booking_from_transaction(tx)
        else:
            # Payment failed
            return request.render('hotel_website_integration.website_hotel_payment_failed', {
                'tx': tx,
                'error': 'Payment was not successful'
            })

    def _create_booking_from_transaction(self, tx):
        """Create hotel booking from successful payment transaction"""
        try:
            # Look for existing booking with this transaction reference
            Book = request.env['room.booking'].sudo()
            existing_booking = Book.search([('payment_reference', '=', tx.reference)], limit=1)
            
            if existing_booking:
                # Update existing booking with payment info
                existing_booking.sudo().write({
                    'payment_transaction_id': tx.id,
                    'payment_status': 'paid',
                    'payment_provider_id': tx.provider_id.id,
                    'state': 'reserved',
                })
                booking = existing_booking
            else:
                # Create new booking from transaction
                booking_vals = {
                    'partner_id': tx.partner_id.id,
                    'name': f'Payment Booking - {tx.reference}',
                    'rate': tx.amount,
                    'state': 'reserved',
                    'email': tx.partner_id.email,
                    'phone': tx.partner_id.phone,
                    'payment_transaction_id': tx.id,
                    'payment_status': 'paid',
                    'payment_reference': tx.reference,
                    'payment_provider_id': tx.provider_id.id,
                }
                
                booking = Book.create(booking_vals)
                try:
                    booking.sudo().action_reserve()
                except Exception as e:
                    _logger.warning('Could not confirm booking: %s', e)
            
            return request.render('hotel_website_integration.website_hotel_payment_success', {
                'tx': tx,
                'booking': booking,
            })
            
        except Exception as e:
            _logger.exception('Failed to create booking from transaction: %s', e)
            return request.render('hotel_website_integration.website_hotel_payment_failed', {
                'tx': tx,
                'error': 'Booking creation failed'
            })

    @http.route(['/hotel/payment/providers'], type='http', auth='public', website=True)
    def payment_providers(self, **kw):
        """Show available payment providers"""
        providers = request.env['payment.provider'].sudo().search([('state', 'in', ['enabled', 'test'])])
        return request.render('hotel_website_integration.website_hotel_payment_providers', {
            'providers': providers,
        })

    @http.route(['/hotel/debug/payment'], type='http', auth='public', website=True)
    def debug_payment_providers(self, **kw):
        """Debug route to check payment provider status"""
        providers = request.env['payment.provider'].sudo().search([])
        enabled_providers = request.env['payment.provider'].sudo().search([('state', '=', 'enabled')])

        debug_info = {
            'total_providers': len(providers),
            'enabled_providers': len(enabled_providers),
            'provider_details': []
        }

        for p in providers:
            website_ids = []
            try:
                website_ids = [w.id for w in getattr(p, 'website_ids', []) or []]
            except Exception:
                website_ids = []

            available_currency_ids = []
            try:
                available_currency_ids = [c.id for c in getattr(p, 'available_currency_ids', []) or []]
            except Exception:
                available_currency_ids = []

            debug_info['provider_details'].append({
                'id': p.id,
                'name': p.name,
                'state': p.state,
                'code': p.code,
                'website_ids': website_ids,
                'available_currency_ids': available_currency_ids,
            })

        return request.render('hotel_website_integration.debug_payment_info', {
            'debug_info': debug_info,
        })