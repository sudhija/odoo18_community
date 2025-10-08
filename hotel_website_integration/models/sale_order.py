import logging
from odoo import api, models
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    # def action_confirm(self):
    #     res = super(SaleOrder, self).action_confirm()
    #     for order in self:
    #         if order.order_line.filtered(lambda l: l.room_id):
    #             try:
    #                 order.env['room.booking'].create_reservation_from_sale_order(order)
    #             except Exception as e:
    #                 _logger.warning('Could not create hotel reservation for SO %s: %s', order.id, e)
    #     return res
    
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            # Create a room.booking per order if any room lines exist
            room_lines = order.order_line.filtered(lambda l: l.room_id and l.checkin and l.checkout)
            if not room_lines:
                continue
            try:
                # Derive a single booking using min checkin and max checkout
                checkins = [l.checkin for l in room_lines]
                checkouts = [l.checkout for l in room_lines]
                checkin_date = min(checkins)
                checkout_date = max(checkouts)

                booking_vals = {
                    'partner_id': order.partner_id.id,
                    'checkin_date': fields.Datetime.to_datetime(str(checkin_date)),
                    'checkout_date': fields.Datetime.to_datetime(str(checkout_date)),
                    'need_food': False,
                    'need_service': False,
                    'need_fleet': False,
                    'need_event': False,
                }
                booking = self.env['room.booking'].sudo().create(booking_vals)

                # Create booking lines
                for line in room_lines:
                    nights = max(1, (line.checkout - line.checkin).days)
                    self.env['room.booking.line'].sudo().create({
                        'booking_id': booking.id,
                        'room_id': line.room_id.id,
                        'checkin_date': fields.Datetime.to_datetime(str(line.checkin)),
                        'checkout_date': fields.Datetime.to_datetime(str(line.checkout)),
                        'uom_qty': nights,
                    })
                # Optionally reserve immediately
                # booking.action_reserve()
            except Exception as e:
                _logger.exception('Failed to create room.booking for SO %s: %s', order.id, e)
        return res
