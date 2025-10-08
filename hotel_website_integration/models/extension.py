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