# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd. (modified)
#
###############################################################################
from datetime import datetime, timedelta
import logging
from odoo import http, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class TableReservation(http.Controller):
    """ For reservation of tables """

    # ------------------------------
    # Helpers
    # ------------------------------
    def _time_to_minutes(self, time_val):
        if isinstance(time_val, (float, int)):
            hours = int(time_val)
            minutes = int((time_val - hours) * 60)
            return hours * 60 + minutes
        elif isinstance(time_val, str):
            t = self._parse_time(time_val)
            return t.hour * 60 + t.minute if t else 0
        return 0

    def _float_to_time(self, hour_float):
        hours = int(hour_float)
        minutes = int((hour_float - hours) * 60)
        dt = datetime.strptime(f"{hours:02d}:{minutes:02d}", "%H:%M")
        return dt.strftime("%I:%M %p")

    def _parse_time(self, value):
        """Try parsing time in both 12h and 24h formats → return datetime.time or None"""
        if not value:
            return None
        value = str(value).strip()
        for fmt in ("%I:%M %p", "%H:%M"):
            try:
                return datetime.strptime(value, fmt).time()
            except Exception:
                continue
        return None

    # ------------------------------
    # Routes
    # ------------------------------
    @http.route(['/table_reservation'], type='http', auth='public', website=True)
    def table_reservation(self):
        pos_config = request.env['res.config.settings'].sudo().search([], limit=1)
        try:
            opening_val = pos_config.pos_opening_hour
            closing_val = pos_config.pos_closing_hour

            opening_minutes = self._time_to_minutes(opening_val)
            closing_minutes = self._time_to_minutes(closing_val)

            opening_hour = (self._float_to_time(float(opening_val))
                            if isinstance(opening_val, (float, int)) else opening_val)
            closing_hour = (self._float_to_time(float(closing_val))
                            if isinstance(closing_val, (float, int)) else closing_val)

        except Exception as e:
            _logger.error("Error parsing opening/closing hours: %s", e)
            opening_hour, closing_hour = "10:00 AM", "06:00 PM"
            opening_minutes, closing_minutes = 600, 1080

        return request.render("table_reservation_on_website.table_reservation", {
            'opening_hour': opening_hour,
            'closing_hour': closing_hour,
            'opening_minutes': opening_minutes,
            'closing_minutes': closing_minutes,
        })

    @http.route(['/restaurant/floors'], type='http', auth='public', website=True, methods=['POST'])
    def restaurant_floors(self, **kwargs):
        """Get floor details and check if the slot is already booked (checks table.reservation)"""
        floors = request.env['restaurant.floor'].sudo().search([])
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        refund = request.env['ir.config_parameter'].sudo().get_param(
            'table_reservation_on_website.refund')

        date = kwargs.get('date')
        start_time = kwargs.get('start_time')
        end_time = kwargs.get('end_time')
        floor_id = kwargs.get('floors')

        already_booked = False
        booked_table_names = []
        available_count = 0

        # Only check when all necessary params are present
        if date and start_time and end_time and floor_id:
            # parse date
            try:
                date_obj = datetime.strptime(date, "%Y-%m-%d").date()
            except Exception:
                date_obj = None

            # parse requested slot times into time objects
            s_time = self._parse_time(start_time)
            e_time = self._parse_time(end_time)

            # get all tables for the floor
            try:
                floor_id_int = int(floor_id)
                tables_all = request.env['restaurant.table'].sudo().search([('floor_id', '=', floor_id_int)])
            except Exception:
                tables_all = request.env['restaurant.table'].sudo().search([('floor_id', '=', floor_id)])

            # find reservations that day for that floor
            reservations = request.env['table.reservation'].sudo().search([
                ('floor_id', '=', floor_id),
                ('date', '=', date_obj),
                ('state', '=', 'reserved')
            ])

            booked_table_ids = set()
            # check overlap for each reservation
            for rec in reservations:
                rec_s = self._parse_time(rec.starting_at)
                rec_e = self._parse_time(rec.ending_at)
                if s_time and e_time and rec_s and rec_e:
                    # overlap if requested_start < rec_end AND requested_end > rec_start
                    if (s_time < rec_e) and (e_time > rec_s):
                        booked_table_ids.update(rec.booked_tables_ids.ids)
                        booked_table_names += rec.booked_tables_ids.mapped('name')

            # compute available tables count
            all_table_ids = set(tables_all.ids)
            available_ids = all_table_ids - booked_table_ids
            available_count = len(available_ids)

            if available_count == 0:
                already_booked = True

        vals = {
            'floors': floors,
            'date': date,
            'start_time': start_time,
            'end_time': end_time,
            'payment': payment,
            'refund': refund,
            'already_booked': already_booked,
            'booked_tables': booked_table_names,
            'available_count': available_count,
        }
        return request.render("table_reservation_on_website.restaurant_floors", vals)

    @http.route(['/restaurant/floors/tables'], type='json', auth='public', website=True)
    def restaurant_floors_tables(self, **kwargs):
        """ To get non-reserved table details (AJAX) """
        try:
            floor_id = int(kwargs.get('floors_id'))
        except Exception:
            return {}

        table_inbetween = []
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        tables = request.env['restaurant.table'].sudo().search([('floor_id', '=', floor_id)])

        # parse date
        date_raw = kwargs.get('date')
        try:
            date_obj = datetime.strptime(date_raw, "%Y-%m-%d").date() if date_raw else None
        except Exception:
            date_obj = None

        reserved = request.env['table.reservation'].sudo().search(
            [('floor_id', '=', floor_id), ('date', '=', date_obj), ('state', '=', 'reserved')]
        )

        # Parse incoming start time (user selection)
        start_time_new = self._parse_time(kwargs.get("start") or kwargs.get("start_time"))

        for rec in reserved:
            start_time = self._parse_time(rec.starting_at)
            end_time = self._parse_time(rec.ending_at)

            if start_time and end_time and start_time_new:
                # adjust with lead time if applicable
                start_at = (datetime.combine(date_obj, start_time) -
                            timedelta(hours=int(rec.lead_time),
                                      minutes=int((rec.lead_time % 1) * 100))).time()

                if start_at <= start_time_new <= end_time:
                    for table in rec.booked_tables_ids:
                        table_inbetween.append(table.id)

        data_tables = {}
        for rec in tables:
            if rec.id not in table_inbetween:
                data_tables[rec.id] = {
                    'id': rec.id,
                    'name': rec.display_name,  # ✅ use display_name
                    'seats': rec.seats,
                    'rate': rec.rate if payment else 0,
                }
        return data_tables

    @http.route(['/booking/confirm'], type="http", auth="public", csrf=False, website=True, methods=['POST'])
    def booking_confirm(self, **kwargs):
        """ For booking tables — requires login at confirmation """
        _logger.info("booking_confirm called with kwargs: %s", {k: kwargs.get(k) for k in ('date','start_time','end_time','tables','floors')})

        # Ensure user is logged in
        if request.env.user._is_public():
            # Store booking details in session before redirecting to login
            request.session['pending_booking'] = kwargs
            return request.redirect('/web/login?redirect=/booking/after_login')

        company = request.env.company

        if not kwargs.get("tables"):
            return request.make_response("No tables selected", headers=[('Content-Type', 'text/plain')], status=400)

        # parse table ids
        try:
            list_tables = [int(rec) for rec in kwargs.get("tables").split(',') if rec]
            record_tables = request.env['restaurant.table'].sudo().search([('id', 'in', list_tables)])
        except Exception as e:
            _logger.exception("Failed to parse tables: %s", e)
            return request.make_response("Invalid table selection", headers=[('Content-Type', 'text/plain')], status=400)

        # parse start/end times into 24h format
        start_str = (kwargs.get("start_time") or "").strip()
        end_str = (kwargs.get("end_time") or "").strip()
        try:
            start_dt = datetime.strptime(start_str, "%I:%M %p")
            end_dt = datetime.strptime(end_str, "%I:%M %p")
            start_24 = start_dt.strftime("%H:%M")
            end_24 = end_dt.strftime("%H:%M")
        except Exception:
            _logger.exception("Failed to parse start/end times: start=%s end=%s", start_str, end_str)
            return request.make_response("Invalid time format. Please use the booking UI to select times.", headers=[('Content-Type', 'text/plain')], status=400)

        # final sanity: prevent past date/time
        date_str = kwargs.get('date')
        try:
            sel_dt = datetime.strptime(f"{date_str} {start_24}", "%Y-%m-%d %H:%M")
            if sel_dt < datetime.now():
                return request.make_response("Selected date/time is in the past.", headers=[('Content-Type', 'text/plain')], status=400)
        except Exception:
            _logger.warning("Could not validate date/time for past check: date=%s start=%s", date_str, start_24)

        # 🔹 Conflict check: already reserved?
        overlapping = request.env['table.reservation'].sudo().search([
            ('date', '=', date_str),
            ('state', '=', 'reserved'),
            ('booked_tables_ids', 'in', record_tables.ids),
            ('starting_at', '<', end_24),
            ('ending_at', '>', start_24),
        ], limit=1)

        if overlapping:
            msg = f"Sorry, table(s) {', '.join(overlapping.booked_tables_ids.mapped('name'))} are already booked from {overlapping.starting_at} to {overlapping.ending_at}."
            return request.make_response(msg, headers=[('Content-Type', 'text/plain')], status=400)

        # ✅ No conflict → continue with normal flow...
        try:
            payment = request.env['ir.config_parameter'].sudo().get_param("table_reservation_on_website.reservation_charge")
            amount = [rec.rate for rec in record_tables]

            if payment:
                table_product = request.env.ref('table_reservation_on_website.product_product_table_booking').sudo()
                table_product.write({'list_price': sum(amount)})
                sale_order = request.website.sale_get_order(force_create=True)
                if sale_order.state != 'draft':
                    request.session['sale_order_id'] = None
                    sale_order = request.website.sale_get_order(force_create=True)
                sale_order.sudo().write({
                    'tables_ids': record_tables,
                    'floors': kwargs.get('floors'),
                    'date': kwargs.get('date'),
                    'starting_at': start_24,
                    'ending_at': end_24,
                    'booking_amount': sum(amount),
                    'order_line': [(0, 0, {
                        'name': table_product.name,
                        'product_id': table_product.id,
                        'product_uom_qty': 1,
                        'price_unit': sum(amount),
                    })],
                })
                sale_order.website_id = request.env['website'].sudo().search([('company_id', '=', company.id)], limit=1)
                return request.redirect("/shop/cart")

            else:
                reservation = request.env['table.reservation'].sudo().create({
                    "customer_id": request.env.user.partner_id.id,
                    "booked_tables_ids": [(6, 0, record_tables.ids)],
                    "floor_id": kwargs.get('floors'),
                    "date": kwargs.get('date'),
                    "starting_at": start_24,
                    "ending_at": end_24,
                    'booking_amount': 0,
                    'state': 'reserved',
                    'type': 'website',
                })
                return request.render('table_reservation_on_website.reservation_success_page', {
                    'reservation': reservation,
                    'company': company,
                    'tables': record_tables,
                })

        except Exception:
            _logger.exception("Unexpected error while processing booking_confirm.")
            return request.make_response("Unexpected server error while processing booking.", headers=[('Content-Type', 'text/plain')], status=500)

    @http.route(['/table/reservation/pos'], type='json', auth='user', website=True)
    def table_reservation_pos(self, table_id):
        """ For pos table booking """
        table = request.env['restaurant.table'].sudo().browse(table_id)
        date_and_time = datetime.now()
        starting_at = (date_and_time + timedelta(hours=5, minutes=30)).time().strftime("%H:%M")
        end_time = (date_and_time + timedelta(hours=6, minutes=30)).time().strftime("%H:%M")
        payment = request.env['ir.config_parameter'].sudo().get_param(
            "table_reservation_on_website.reservation_charge")
        vals = {
            'floor_id': table.floor_id.id,
            'booked_tables_ids': table,
            'date': date_and_time.date(),
            'starting_at': starting_at,
            'ending_at': end_time,
            'booking_amount': table.rate if payment else 0,
            'state': 'reserved',
            'type': 'pos'
        }
        request.env['table.reservation'].sudo().create(vals)
        return {}

    @http.route(['/active/floor/tables'], type='json', auth='user', website=True)
    def active_floor_tables(self, floor_id):
        """ To get active floors """
        table_inbetween = []
        product_id = request.env.ref('table_reservation_on_website.product_product_table_booking_pos')
        for rec in request.env['pos.category'].sudo().search([]):
            if rec:
                product_id.pos_categ_ids = [(4, rec.id, 0)]

        table_reservation = request.env['table.reservation'].sudo().search([
            ('floor_id', "=", floor_id),
            ('date', '=', datetime.now().date()),
            ('state', '=', 'reserved')
        ])
        for rec in table_reservation:
            try:
                start_time = datetime.strptime(rec.starting_at, "%H:%M")
            except Exception:
                try:
                    start_time = datetime.strptime(rec.starting_at, "%I:%M %p")
                except Exception:
                    start_time = None

            if start_time:
                start_at = start_time - timedelta(
                    hours=int(rec.lead_time),
                    minutes=int((rec.lead_time % 1) * 100)
                )
                try:
                    end_at = datetime.strptime(rec.ending_at, "%H:%M").time()
                except Exception:
                    try:
                        end_at = datetime.strptime(rec.ending_at, "%I:%M %p").time()
                    except Exception:
                        end_at = None

                now = (datetime.now() + timedelta(hours=5, minutes=30)).time().strftime("%H:%M")
                try:
                    if start_at.time() <= datetime.strptime(now, "%H:%M").time() <= end_at:
                        for table in rec.booked_tables_ids:
                            table_inbetween.append(table.id)
                except Exception:
                    # ignore parse issues for now
                    continue
        return table_inbetween

    @http.route(['/booking/after_login'], type='http', auth='user', website=True)
    def booking_after_login(self, **kwargs):
        """Process the booking automatically after login."""
        pending_data = request.session.pop('pending_booking', None)
        if not pending_data:
            # No pending data — just go to the reservation page
            return request.redirect('/table_reservation')

        # Reuse the same booking_confirm logic with stored data
        return self.booking_confirm(**pending_data)
