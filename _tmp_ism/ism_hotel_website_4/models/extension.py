from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)
from datetime import timedelta, date as pydate

class WebsiteFacility(models.Model):
    _name = "website.hotel.facility"
    _description = "Website Facility"
    name = fields.Char(required=True)
    icon = fields.Char()

class WebsiteRoomImage(models.Model):
    _name = "website.hotel.room.image"
    _description = "Website Room Image"
    _order = "sequence, id"
    room_id = fields.Many2one("hotel.room", required=True, ondelete="cascade")
    image_1920 = fields.Image(required=True, max_width=1920, max_height=1080)
    sequence = fields.Integer(default=10)

class WebsiteRoomPrice(models.Model):
    _name = "website.hotel.room.price"
    _description = "Room price rule by date"
    _order = "date_from"
    room_id = fields.Many2one("hotel.room", required=True, ondelete="cascade")
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    price = fields.Float(required=True)

    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        for rec in self:
            if rec.date_to < rec.date_from:
                raise ValidationError(_("date_to must be on/after date_from."))

class HotelRoom(models.Model):
    _inherit = "hotel.room"

    cover_image = fields.Image(max_width=1920, max_height=1080)
    facility_ids = fields.Many2many("website.hotel.facility", string="Facilities")
    gallery_image_ids = fields.One2many("website.hotel.room.image", "room_id", string="Gallery")
    base_price = fields.Float(default=0.0, help="Default nightly rate")
    tax_percent = fields.Float(default=12.0)
    price_rule_ids = fields.One2many("website.hotel.room.price", "room_id", string="Price Rules")
    max_guests = fields.Integer(string='Max Guests', default=2)
    is_published = fields.Boolean("Visible on Website", default=False)
    website_category_id = fields.Many2one("product.category", string="Website Category")

    def is_available(self, checkin, checkout, guests=1):
        self.ensure_one()
        # quick guards
        if not checkin or not checkout or checkin >= checkout:
            return False
        # guest capacity check
        if self.max_guests and guests > self.max_guests:
            return False
        # overlap check (hotel.book.history uses room_id, not room_ids)
        Booking = self.env["hotel.book.history"].sudo()
        overlapping = Booking.search([
            ("room_id", "=", self.id),
            ("check_in", "<", checkout),
            ("check_out", ">", checkin),
            ("state", "in", ["booked", "checked_in"]),
        ], limit=1)
        return not bool(overlapping)

    def get_rate_for_dates(self, checkin, checkout):
        """Accepts date/datetime/date-string; returns average nightly rate across nights."""
        self.ensure_one()
        Rule = self.env["website.hotel.room.price"].sudo()

        # normalize to dates
        def _to_date(d):
            if isinstance(d, pydate):
                return d
            return fields.Date.from_string(d)
        start = _to_date(checkin)
        end = _to_date(checkout)

        total = 0.0
        nights = 0
        d = start
        while d < end:
            rule = Rule.search([
                ("room_id", "=", self.id),
                ("date_from", "<=", d),
                ("date_to", ">=", d)
            ], limit=1)
            nightly = rule.price if rule else (self.base_price or (self.room_type and self.room_type.list_price) or 0.0)
            total += nightly
            nights += 1
            d = d + timedelta(days=1)
        return (total / nights) if nights else (self.base_price or (self.room_type and self.room_type.list_price) or 0.0)

class HotelBooking(models.Model):
    _inherit = "hotel.book.history"

    rate = fields.Float(string="Nightly Rate")
    discount_amount = fields.Float(default=0.0)
    guests = fields.Integer(default=2)
    email = fields.Char()
    phone = fields.Char()
    special_requests = fields.Text()
    nights = fields.Integer(compute="_compute_nights", store=False)
    amount_untaxed = fields.Float(compute="_compute_amounts", store=False)
    tax_amount = fields.Float(compute="_compute_amounts", store=False)
    amount_total = fields.Float(compute="_compute_amounts", store=False)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('booked', 'Booked'),
        ('checked_in', 'Checked In'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled'),
    ], default='draft')
    
    # Payment related fields
    payment_transaction_id = fields.Many2one('payment.transaction', string='Payment Transaction')
    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], default='pending', string='Payment Status')
    payment_reference = fields.Char(string='Payment Reference')
    payment_provider_id = fields.Many2one('payment.provider', string='Payment Provider')

    @api.constrains('check_in', 'check_out')
    def _check_dates(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                if rec.check_in < fields.Date.today():
                    raise ValidationError(_("Past dates are not allowed"))
                if rec.check_out <= rec.check_in:
                    raise ValidationError(_("Check-out must be after check-in"))

    @api.depends("nights", "rate", "discount_amount", "room_id")
    def _compute_amounts(self):
        for r in self:
            subtotal = (r.nights or 0) * (r.rate or 0) - (r.discount_amount or 0)
            r.amount_untaxed = max(subtotal, 0.0)
            tax_percent = (r.room_id.tax_percent or 0.0) if r.room_id else 0.0
            r.tax_amount = r.amount_untaxed * tax_percent / 100.0
            r.amount_total = r.amount_untaxed + r.tax_amount

    @api.depends('check_in', 'check_out')
    def _compute_nights(self):
        for rec in self:
            if rec.check_in and rec.check_out:
                rec.nights = max(1, (rec.check_out - rec.check_in).days)
            else:
                rec.nights = 0

    @api.constrains('guests', 'room_id')
    def _check_guest_capacity(self):
        for rec in self:
            if rec.room_id:
                max_allowed = getattr(rec.room_id, 'max_allowed_person', None) or rec.room_id.max_guests
                if rec.guests and max_allowed and rec.guests > max_allowed:
                    raise ValidationError(
                        _("Room %s allows a maximum of %s guests, but you selected %s.")
                        % (rec.room_id.name, max_allowed, rec.guests)
                    )

    def action_confirm(self):
        self.write({'state': 'booked'})
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    room_id = fields.Many2one('hotel.room', string='Room')
    checkin = fields.Date('Check-in')
    checkout = fields.Date('Check-out')
    guests = fields.Integer('Guests')
    special_requests = fields.Text('Special Requests')
    is_hotel_booking = fields.Boolean('Is Hotel Booking', default=False)

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'duration')
    def _compute_amount(self):
        """Override _compute_amount to preserve custom prices for hotel bookings"""
        for line in self:
            if line.is_hotel_booking:
                # For hotel bookings, use standard Odoo computation without duration multiplier
                # This bypasses the ism_hotel module's duration logic
                tax_base_line_dict = line._convert_to_tax_base_line_dict()
                # Don't multiply by duration for hotel bookings
                tax_results = self.env['account.tax']._compute_taxes([tax_base_line_dict])
                totals = list(tax_results['totals'].values())[0]
                amount_untaxed = totals['amount_untaxed']
                amount_tax = totals['amount_tax']

                line.update({
                    'price_subtotal': amount_untaxed,
                    'price_tax': amount_tax,
                    'price_total': amount_untaxed + amount_tax,
                })
                _logger.info('Preserved hotel booking price in _compute_amount: %s (subtotal: %s)', line.price_unit, amount_untaxed)
            else:
                # For regular lines, use the inherited method (which may include duration logic from ism_hotel)
                super(SaleOrderLine, line)._compute_amount()

    @api.onchange('product_id')
    def product_id_change(self):
        """Override product_id_change to preserve custom prices for hotel bookings"""
        if self.is_hotel_booking:
            # Don't recompute price for hotel bookings
            _logger.info('Skipping product_id_change for hotel booking to preserve custom price: %s', self.price_unit)
            return
        else:
            # For regular products, use standard behavior
            super().product_id_change()

    def write(self, vals):
        """Override write to prevent price_unit changes for hotel bookings"""
        if 'price_unit' in vals and self.is_hotel_booking:
            # Don't allow price_unit changes for hotel bookings
            _logger.info('Preventing price_unit change for hotel booking from %s to %s', self.price_unit, vals['price_unit'])
            vals = vals.copy()
            del vals['price_unit']
        return super().write(vals)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        Book = self.env['hotel.book.history'].sudo()
        for order in self:
            for line in order.order_line:
                if line.room_id:
                    existing = Book.search([
                        ('partner_id', '=', order.partner_id.id),
                        ('room_id', '=', line.room_id.id),
                        ('check_in', '=', line.checkin),
                        ('check_out', '=', line.checkout),
                    ], limit=1)
                    if existing:
                        continue
                    try:
                        vals = {
                            'partner_id': order.partner_id.id,
                            'check_in': line.checkin,
                            'check_out': line.checkout,
                            'room_id': line.room_id.id,
                            'name': _('Website Booking'),
                            'rate': line.price_unit,
                            'discount_amount': 0.0,
                            'guests': line.guests or 1,
                            'email': order.partner_id.email,
                            'phone': order.partner_id.phone,
                            'special_requests': line.special_requests,
                        }
                        booking = Book.create(vals)
                        booking.sudo().action_confirm()
                        _logger.info('Successfully created booking for order %s line %s', order.id, line.id)
                    except Exception as e:
                        _logger.exception(
                            'Failed to create booking for order %s line %s: %s',
                            order.id, line.id, e
                        )
        return res
