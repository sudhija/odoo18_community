from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
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
