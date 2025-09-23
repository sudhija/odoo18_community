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
        # overlap check against room.booking.line in states that block availability
        Line = self.env['room.booking.line'].sudo()
        overlapping = Line.search([
            ('room_id', '=', self.id),
            ('booking_id.state', 'in', ['reserved', 'check_in']),
            ('checkin_date', '<', checkout),
            ('checkout_date', '>', checkin),
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
    # Align with existing backend by extending room.booking (no extra fields required here)
    _inherit = "room.booking"
