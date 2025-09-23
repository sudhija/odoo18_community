from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _cart_update(self, product_id=None, line_id=None, add_qty=0, set_qty=0, **kwargs):
        res = super()._cart_update(product_id=product_id, line_id=line_id, add_qty=add_qty, set_qty=set_qty, **kwargs)
        line = self.env['sale.order.line'].browse(res.get('line_id'))
        if line and line.room_id:
            # Preserve custom booking subtotal
            if kwargs.get('price_unit'):
                line.price_unit = kwargs['price_unit']
        return res


