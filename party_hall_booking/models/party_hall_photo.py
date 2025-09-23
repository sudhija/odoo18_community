from odoo import models, fields

class PartyHallPhoto(models.Model):
    _name = 'party.hall.photo'
    _description = 'Party Hall Photo'

    name = fields.Char(default='Photo')
    image_1920 = fields.Image("Photo", required=True)
    hall_id = fields.Many2one('party.hall', string='Hall', required=True, ondelete='cascade')

    