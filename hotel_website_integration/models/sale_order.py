import logging
from odoo import api, models, fields
_logger = logging.getLogger(__name__)

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def ensure_pricelist(self):
        """Ensure the sale order has a valid pricelist_id. Tries order -> partner -> company -> product.list0.
        If none exists, create a minimal pricelist to avoid NOT NULL DB errors when creating bookings.
        """
        for order in self:
            if order.pricelist_id:
                continue
            # Try partner's default
            if order.partner_id and order.partner_id.property_product_pricelist:
                order.pricelist_id = order.partner_id.property_product_pricelist
                continue
            # Try company default currency/pricelist lookup
            try:
                pl = self.env.ref('product.list0')
                if pl:
                    order.pricelist_id = pl
                    continue
            except Exception:
                pass
            # Last resort: create a minimal pricelist
            try:
                currency = order.company_id.currency_id or self.env.company.currency_id
                pl_created = self.env['product.pricelist'].create({
                    'name': f'Default pricelist for {order.company_id.name or "Company"}',
                    'currency_id': currency.id,
                })
                order.pricelist_id = pl_created
            except Exception as e:
                _logger.exception('Could not create fallback pricelist: %s', e)
                # let the caller handle absence of pricelist
        return True

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
        try:
            res = super(SaleOrder, self).action_confirm()
        except Exception as e:
            _logger.exception('Exception during super(SaleOrder).action_confirm(): %s', e)
            raise
        for order in self:
            # Create a room.booking per order if any room lines exist
            room_lines = order.order_line.filtered(lambda l: l.room_id and l.checkin and l.checkout)
            if not room_lines:
                continue
            try:
                # Ensure the sale order has a valid pricelist before creating bookings
                try:
                    order.ensure_pricelist()
                except Exception:
                    _logger.exception('Could not ensure pricelist for order %s', order.id)
                    # continue and let the later create raise a clear error
                
                # Derive a single booking using min checkin and max checkout
                checkins = [l.checkin for l in room_lines]
                checkouts = [l.checkout for l in room_lines]
                checkin_date = min(checkins)
                checkout_date = max(checkouts)

                # Ensure required fields are provided: company_id and pricelist_id
                # Use the pricelist now present on the order
                pricelist = order.pricelist_id.id if order.pricelist_id else None
                if not pricelist:
                    # As a final fallback, try to ensure pricelist programmatically
                    try:
                        order.ensure_pricelist()
                        pricelist = order.pricelist_id.id if order.pricelist_id else None
                    except Exception:
                        _logger.exception('Final attempt to ensure pricelist failed for order %s', order.id)

                booking_vals = {
                    'partner_id': order.partner_id.id,
                    'company_id': order.company_id.id,
                    'checkin_date': fields.Datetime.to_datetime(str(checkin_date)),
                    'checkout_date': fields.Datetime.to_datetime(str(checkout_date)),
                    'need_food': False,
                    'need_service': False,
                    'need_fleet': False,
                    'need_event': False,
                    'sale_order_id': order.id,
                    'pricelist_id': pricelist,
                }
                _logger.info('Creating booking with vals: %s', booking_vals)
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
                booking.action_reserve()
            except Exception as e:
                # Log and re-raise so the original exception is visible in server logs
                _logger.exception('Failed to create room.booking for SO %s: %s', order.id, e)
                raise
        return res
