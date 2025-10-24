from odoo import api, SUPERUSER_ID

def post_init_hook(registry):
    """Populate product_id for existing hotel rooms."""
    with registry.cursor() as cr:
        env = api.Environment(cr, SUPERUSER_ID, {})
        rooms = env["hotel.room"].search([])
        for room in rooms:
            if not room.product_id:
                product = getattr(room.room_type, "product_id", False) or None
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
                        "product_tmpl_id": product.product_tmpl_id.id if product.product_tmpl_id else False,
                    })
                    room.fix_website_flags()

# from odoo import api, SUPERUSER_ID

# def post_init_hook(cr, registry):
#     """Populate product_id for existing hotel rooms."""
#     env = api.Environment(cr, SUPERUSER_ID, {})
#     rooms = env["hotel.room"].search([])
#     Product = env["product.product"]

#     for room in rooms:
#         if not room.product_id:
#             # Try linking from room_type if product exists
#             product = None
#             if getattr(room, "room_type", False):
#                 rt = room.room_type
#                 product = getattr(rt, "product_id", False) or getattr(rt, "product_tmpl_id", False)
#                 if product and product._name == "product.template":
#                     product = product.product_variant_ids[:1] or None

#             # Otherwise, create a new product
#             if not product:
#                 product_tmpl = env["product.template"].sudo().create({
#                     "name": room.name or f"Room {room.id}",
#                     "type": "service",
#                     "sale_ok": True,
#                     "website_published": True,
#                     "list_price": getattr(room, "base_price", 0.0) or 0.0,
#                     "categ_id": room.website_category_id.id if room.website_category_id else False,
#                 })
#                 product = product_tmpl.product_variant_ids[:1] or None

#             room.sudo().write({
#                 "product_id": product.id,
#                 "product_tmpl_id": product.product_tmpl_id.id,
#             })
#             if product:
#                 room.fix_website_flags()    