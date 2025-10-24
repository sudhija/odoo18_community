from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta, date as pydate

class HotelRoom(models.Model):
    _inherit = "hotel.room"

    cover_image = fields.Image(max_width=1920, max_height=1080)
    facility_ids = fields.Many2many("website.hotel.facility", string="Facilities")
    gallery_image_ids = fields.One2many("website.hotel.room.image", "room_id", string="Gallery")
    #base_price = fields.Float(default=0.0, help="Default nightly rate")
    #tax_percent = fields.Float(default=12.0)
    price_rule_ids = fields.One2many("website.hotel.room.price", "room_id", string="Price Rules")
    max_guests = fields.Integer(string='Max Guests', default=2)
    is_published = fields.Boolean("Visible on Website", default=False)
    website_category_id = fields.Many2one("product.category", string="Website Category")
    product_id = fields.Many2one('product.product', string='Product Variant')
    product_tmpl_id = fields.Many2one('product.template', string='Product Template')
    amenity_ids = fields.Many2many('hotel.amenity','hotel_room_amenity_rel','room_id','amenity_id', string="Amenities")

    @api.model
    def create(self, vals):
        # Handle multi-language name if exists
        name_to_check = vals.get('name')
        if isinstance(name_to_check, dict):
            lang = self.env.lang or 'en_US'
            name_to_check = name_to_check.get(lang, list(name_to_check.values())[0])

        # Check for duplicate room name
        if self.env['hotel.room'].search([('name', '=', name_to_check)]):
            raise UserError(_("A room with the name '%s' already exists. Please choose a different name.") % name_to_check)
        room = super().create(vals)
        # Only create product if it doesn't already exist
        if not room.product_id:
            product_tmpl = self.env['product.template'].sudo().create({
                'name': room.name or f"Room {room.id}",
                'type': 'service',
                'sale_ok': True,
                'purchase_ok': False,
                'website_published': True,
                'list_price': room.list_price,
                'taxes_id': [],  
            })
            room.product_tmpl_id = product_tmpl.id
            room.product_id = product_tmpl.product_variant_ids[:1].id
        return room

    def fix_website_flags(self):
        for room in self:
            if room.product_id:
                product = room.product_id
                # Make sure the product is published for website sale
                product.sudo().write({
                    'available_on_website': True,
                    'website_published': True,
                    'sale_ok': True,
                    'list_price': product.list_price or 100.0
                })

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
    @api.constrains('name')
    def _check_unique_room_name(self):
        for record in self:
            existing = self.search([('name', '=', record.name), ('id', '!=', record.id)], limit=1)
            if existing:
                raise ValidationError(_("Room name '%s' already exists!") % record.name)

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
            nightly = rule.price if rule else ((self.room_type and self.room_type.list_price) or 0.0)
            total += nightly
            nights += 1
            d = d + timedelta(days=1)
        return (total / nights) if nights else ((self.room_type and self.room_type.list_price) or 0.0)
        _sql_constraints = [('unique_room_name', 'unique(name)', 'Room name must be unique!'),]
