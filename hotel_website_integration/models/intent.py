from odoo import models, fields


class HotelBookingIntent(models.Model):
    _name = 'hotel.booking.intent'
    _description = 'Pre-payment Hotel Booking Intent'
    _rec_name = 'reference'

    reference = fields.Char(required=True, index=True)
    partner_id = fields.Many2one('res.partner', required=True)
    room_id = fields.Many2one('hotel.room', required=True)
    checkin_date = fields.Date(required=True)
    checkout_date = fields.Date(required=True)
    guests = fields.Integer(default=1)
    nights = fields.Integer(default=1)
    rate = fields.Float()
    amount_total = fields.Float()
    special_requests = fields.Text()



