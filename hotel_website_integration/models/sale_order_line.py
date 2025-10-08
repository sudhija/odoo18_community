import logging
import re
from datetime import datetime, timedelta, date
from odoo import http, fields, models, _
from odoo.http import request

_logger = logging.getLogger(__name__)

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    room_id = fields.Many2one('hotel.room', string='Room')
    checkin = fields.Date('Check-in')
    checkout = fields.Date('Check-out')
    guests = fields.Integer('Guests')
    special_requests = fields.Text('Special Requests')