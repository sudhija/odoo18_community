from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HotelReservation(models.Model):
    _name = 'hotel.reservation'
    _description = 'Hotel Reservation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    name = fields.Char(string='Reservation Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    checkin_date = fields.Datetime(string='Check-In', required=True, tracking=True)
    checkout_date = fields.Datetime(string='Check-Out', required=True, tracking=True)
    guests_count = fields.Integer(string='Guests', required=True, default=1)
    special_requests = fields.Text(string='Special Requests')

    sale_order_id = fields.Many2one('sale.order', string='Sale Order', readonly=True, tracking=True)
    room_booking_id = fields.Many2one('room.booking', string='Room Booking', readonly=True, tracking=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, tracking=True)
    payment_transaction_id = fields.Many2one('payment.transaction', string='Payment Transaction', readonly=True, tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', tracking=True)

    payment_status = fields.Selection([
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
    ], string='Payment Status', default='pending', tracking=True)

    reservation_status = fields.Selection([
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Reservation Status', default='active', tracking=True)

    amount_total = fields.Monetary(string='Total Amount', compute='_compute_amount_total', store=True, readonly=True, currency_field='currency_id')
    payment_state = fields.Selection(related='invoice_id.payment_state', string='Invoice Payment State', readonly=True)
    is_paid = fields.Boolean(string='Is Paid', compute='_compute_is_paid', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id', store=True, readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('hotel.reservation') or _('New')
        return super().create(vals)

    @api.depends('sale_order_id', 'sale_order_id.amount_total', 'sale_order_id.currency_id')
    def _compute_amount_total(self):
        for rec in self:
            rec.amount_total = rec.sale_order_id.amount_total if rec.sale_order_id else 0.0

    @api.depends('invoice_id', 'invoice_id.payment_state')
    def _compute_is_paid(self):
        for rec in self:
            rec.is_paid = rec.invoice_id and rec.invoice_id.payment_state == 'paid'

    @api.depends('sale_order_id')
    def _compute_currency_id(self):
        for rec in self:
            rec.currency_id = rec.sale_order_id.currency_id if rec.sale_order_id else self.env.company.currency_id

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirmed'
            rec.reservation_status = 'active'
            if rec.room_booking_id:
                rec.room_booking_id.action_reserve()

    def action_cancel(self):
        for rec in self:
            rec.state = 'cancelled'
            rec.reservation_status = 'cancelled'
            if rec.room_booking_id:
                rec.room_booking_id.action_cancel()

    def _sync_payment_status(self):
        for rec in self:
            if rec.invoice_id:
                if rec.invoice_id.payment_state == 'paid':
                    rec.payment_status = 'paid'
                    rec.state = 'paid'
                    rec.reservation_status = 'active'
                elif rec.invoice_id.payment_state == 'not_paid':
                    rec.payment_status = 'pending'
                    rec.state = 'confirmed'
                elif rec.invoice_id.payment_state == 'in_payment':
                    rec.payment_status = 'pending'
                elif rec.invoice_id.payment_state == 'reversed':
                    rec.payment_status = 'failed'
                    rec.state = 'cancelled'
            elif rec.payment_transaction_id:
                if rec.payment_transaction_id.state == 'done':
                    rec.payment_status = 'paid'
                    rec.state = 'paid'
                elif rec.payment_transaction_id.state == 'pending':
                    rec.payment_status = 'pending'
                elif rec.payment_transaction_id.state == 'cancel':
                    rec.payment_status = 'failed'
                    rec.state = 'cancelled'

    def write(self, vals):
        res = super().write(vals)
        if 'invoice_id' in vals or 'payment_transaction_id' in vals:
            self._sync_payment_status()
        return res

    def unlink(self):
        for rec in self:
            if rec.state == 'paid':
                raise ValidationError(_('Cannot delete a paid reservation.'))
        return super().unlink()
