import logging
from odoo import api, models
_logger = logging.getLogger(__name__)

class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.model_create_multi
    def create(self, vals_list):
        records = super(AccountMove, self).create(vals_list)
        for invoice in records:
            try:
                if invoice.move_type == 'out_invoice' and invoice.invoice_origin:
                    so = invoice.env['sale.order'].search([('name', '=', invoice.invoice_origin)], limit=1)
                    if so:
                        reservation = invoice.env['hotel.reservation'].search([('sale_order_id', '=', so.id)], limit=1)
                        if reservation:
                            invoice.env['room.booking']._link_reservation_to_invoice(reservation.id, invoice.id)
            except Exception:
                _logger.exception('Failed to link reservation to invoice %s', invoice.id)
        return records