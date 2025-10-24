# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Vishnu K P (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import fields, models


class AccountMove(models.Model):
    """Inherited account. move for adding hotel booking reference field to
    invoicing model."""
    _inherit = "account.move"

    hotel_booking_id = fields.Many2one('room.booking',
                                       string="Booking Reference",
                                       readonly=True, help="Choose the Booking"
                                                           "Reference")
    # Compatibility: some accounting views/extensions expect this field
    # to exist on account.move. Provide a lightweight float field so
    # that those views can be parsed without error.
    expected_currency_rate = fields.Float(
        string='Expected Currency Rate',
        help='Optional: expected currency conversion rate for the move',
    )
