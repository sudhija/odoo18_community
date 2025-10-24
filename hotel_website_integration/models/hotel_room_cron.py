from odoo import api, models

class HotelRoomCron(models.Model):
    _inherit = "hotel.room"

    @api.model
    def cron_sync_room_products(self):
        """
        Scheduled action: ensures all hotel.rooms have linked product records.
        """
        env = self.env
        rooms = env["hotel.room"].sudo().search([])

        for room in rooms:
            if not room.product_id:
                # Try to link from room_type if it has a product
                product = None
                if getattr(room, "room_type", False):
                    rt = room.room_type
                    product = getattr(rt, "product_id", False) or getattr(rt, "product_tmpl_id", False)
                    if product and product._name == "product.template":
                        product = product.product_variant_ids[:1] or None

                # Otherwise, create a new product
                if not product:
                    product_tmpl = env["product.template"].sudo().create({
                        "name": room.name or f"Room {room.id}",
                        "type": "service",
                        "sale_ok": True,
                        "website_published": True,
                        "list_price": getattr(room, "base_price", 0.0) or 0.0,
                        "categ_id": room.website_category_id.id if room.website_category_id else False,
                    })
                    product = product_tmpl.product_variant_ids[:1] or None

                if product:
                    room.sudo().write({
                        "product_id": product.id,
                        "product_tmpl_id": product.product_tmpl_id.id,
                    })
                    if hasattr(room, "fix_website_flags"):
                        room.fix_website_flags()

        env.cr.commit()
        _logger = env["ir.logging"]
        _logger.create({
            "name": "Hotel Room Product Sync",
            "type": "server",
            "dbname": env.cr.dbname,
            "level": "INFO",
            "message": "✅ Cron synced all hotel.room product links successfully.",
            "path": "hotel_room_cron",
            "func": "cron_sync_room_products",
            "line": "0",
        })
