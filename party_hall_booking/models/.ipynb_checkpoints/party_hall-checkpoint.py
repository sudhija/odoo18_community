from odoo import models, fields

class PartyHall(models.Model):
    _name = 'party.hall'
    _description = 'Party Hall'

    name = fields.Char(string='Hall Name', required=True)
    image_1920 = fields.Image("Image")
    location = fields.Char(string='Location')
    capacity = fields.Integer(string='Capacity')
    price = fields.Float(string='Price per Slot')
    rating = fields.Float(string='Rating', digits=(2, 1))
    is_recommended = fields.Boolean(string='Recommended')
    halls_count = fields.Integer(string='# Halls', default=1)
    only_veg = fields.Boolean(string='Only-Veg')
    photos_ids = fields.One2many('party.hall.photo', 'hall_id', string='Photos')
    description = fields.Text(string='Description')

    # ✅ New Dynamic Facilities
    facility_ids = fields.Many2many('party.hall.facility', string='Facilities')
