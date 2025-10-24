from odoo import api, fields, models, _

class HotelRoomType(models.Model):
    _name = 'hotel.room.type'
    _description = 'Room Type'

    name = fields.Char("Room Type")
    default_persons = fields.Integer("Default Persons", default=2)
