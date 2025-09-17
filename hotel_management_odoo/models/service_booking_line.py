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
from odoo import api, fields, models, tools


class ServiceBookingLine(models.Model):
    """Model that handles the service booking form"""
    _name = "service.booking.line"
    _description = "Hotel service Line"

    @tools.ormcache()
    def _get_default_uom_id(self):
        """Returns default product uom unit"""
        return self.env.ref('uom.product_uom_unit')

    booking_id = fields.Many2one("room.booking", string="Booking",
                                 help="Indicates the Room Booking",
                                 ondelete="cascade")
    service_id = fields.Many2one('hotel.service', string="Service",
                                 help="Indicates the Service")
    description = fields.Char(string='Description', related='service_id.name',
                              help="Description of the Service")
    uom_qty = fields.Float(string="Qty", default=1.0,
                           help="The quantity converted into the UoM used by "
                                "the product")
    uom_id = fields.Many2one('uom.uom', readonly=True,
                             string="Unit of Measure",
                             help="This will set the unit of measure used",
                             default=_get_default_uom_id)
    price_unit = fields.Float(string='Price', related='service_id.unit_price',
                              digits='Product Price',
                              help="The price of the selected service.")
    tax_ids = fields.Many2many('account.tax',
                               'hotel_service_order_line_taxes_rel',
                               'service_id', 'tax_id',
                               related='service_id.taxes_ids', string='Taxes',
                               help="Default taxes used when selling the "
                                    "services.",
                               domain=[('type_tax_use', '=', 'sale')])
    currency_id = fields.Many2one(string='Currency',
                                  related='booking_id.pricelist_id.currency_id',
                                  help='The currency used')
    price_subtotal = fields.Float(string="Subtotal",
                                  compute='_compute_price_subtotal',
                                  help="Total Price Excluding Tax",
                                  store=True)
    price_tax = fields.Float(string="Total Tax",
                             compute='_compute_price_subtotal',
                             help="Tax Amount",
                             store=True)
    price_total = fields.Float(string="Total",
                               compute='_compute_price_subtotal',
                               help="Total Price Including Tax",
                               store=True)
    state = fields.Selection(related='booking_id.state',
                             string="Order Status",
                             help=" Status of the Order",
                             copy=False)
    booking_line_visible = fields.Boolean(default=False,
                                          string="Booking Line Visible",
                                          help="If true, Booking line will be"
                                               " visible")

    @api.depends('uom_qty', 'price_unit', 'tax_ids')
    def _compute_price_subtotal(self):
        """Compute the amounts of the room booking line."""
        for line in self:
            if line.tax_ids:
                tax_results = line.tax_ids.compute_all(
                    line.price_unit,
                    currency=line.currency_id,
                    quantity=line.uom_qty,
                    product=None,
                    partner=line.booking_id.partner_id
                )
                amount_untaxed = tax_results['total_excluded']
                amount_tax = tax_results['total_included'] - tax_results['total_excluded']
            else:
                amount_untaxed = line.price_unit * line.uom_qty
                amount_tax = 0.0
            
            line.update({
                'price_subtotal': amount_untaxed,
                'price_tax': amount_tax,
                'price_total': amount_untaxed + amount_tax,
            })

    def _convert_to_tax_base_line_dict(self):
        """ Convert the current record to a dictionary in order to use the
         generic taxes computation method
        defined on account.tax.
        :return: A python dictionary."""
        self.ensure_one()
        return self.env['account.tax']._convert_to_tax_base_line_dict(
            self,
            partner=self.booking_id.partner_id,
            currency=self.currency_id,
            taxes=self.tax_ids,
            price_unit=self.price_unit,
            quantity=self.uom_qty,
            price_subtotal=self.price_subtotal,
        )
