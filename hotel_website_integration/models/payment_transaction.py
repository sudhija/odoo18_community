import logging
from odoo import api, models
_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def write(self, vals):
        res = super(PaymentTransaction, self).write(vals)
        for tx in self:
            if 'state' in vals and tx.state == 'done':
                reservation = tx.env['hotel.reservation'].search([('payment_transaction_id', '=', tx.id)], limit=1)
                if reservation:
                    try:
                        reservation._sync_payment_status()
                    except Exception:
                        _logger.exception('Failed to sync payment status for reservation linked to tx %s', tx.id)
        return res