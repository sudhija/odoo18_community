# -*- coding: utf-8 -*-
import json
from odoo import models, fields, api


class CateringOrder(models.Model):
    _name = 'catering.order'
    _description = 'Catering Order'
    _order = 'create_date desc'

    # ----------------------------
    # Customer Details
    # ----------------------------
    customer_name = fields.Char("Customer Name", required=True)
    email = fields.Char("Email")
    phone = fields.Char("Phone")
    address = fields.Text("Address")
    event_date = fields.Date("Event Date")
    service_type = fields.Selection([
        ('takeaway', 'Take Away'),
        ('delivery', 'Delivery & Transportation'),
        ('delivery_suppliers', 'Delivery & Transportation & Suppliers'),
    ], string="Service Type")

    # NEW: number of suppliers (used only when service_type = delivery_suppliers)
    suppliers_count = fields.Integer("Suppliers Count", default=0)

    # ----------------------------
    # Order Info
    # ----------------------------
    menu_selection = fields.Text("Selected Menu Items (JSON)")  # stored as JSON string
    base_total = fields.Float("Base Total", required=True)
    quantity = fields.Integer("Quantity", default=1, required=True)
    final_total = fields.Float("Final Total", compute="_compute_final_total", store=True)

    # ----------------------------
    # System Fields
    # ----------------------------
    sale_order_id = fields.Many2one('sale.order', string="Related Sale Order", readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('quotation', 'Quotation Created'),
        ('sent', 'Quotation Sent'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string="Status", default="draft")

    # ----------------------------
    # Compute Final Total
    # ----------------------------
    @api.depends('base_total', 'quantity')
    def _compute_final_total(self):
        for order in self:
            order.final_total = order.base_total * order.quantity

    # ----------------------------
    # Helpers
    # ----------------------------
    def _get_or_create_product(self, name, price=0.0, ptype='service'):
        """Find a product by exact name. If missing, create a simple product with no taxes."""
        product = self.env['product.product'].search([('name', '=', name)], limit=1)
        if not product:
            tmpl = self.env['product.template'].create({
                'name': name,
                'type': 'service' if ptype == 'service' else 'consu',
                'list_price': price or 0.0,
                'sale_ok': True,
            })
            product = tmpl.product_variant_id
        return product

    # Normalize item payload into a flat list with 'category'
    def _normalize_items(self, raw):
        if isinstance(raw, dict) and 'items' in raw:
            raw = raw.get('items') or []

        def to_flat_items(data):
            flat = []
            if isinstance(data, dict):
                for cat, arr in (data or {}).items():
                    cat_norm = (cat or '').strip().lower()
                    for it in (arr or []):
                        d = dict(it or {})
                        d['category'] = cat_norm
                        flat.append(d)
            elif isinstance(data, list):
                for it in (data or []):
                    d = dict(it or {})
                    d['category'] = (d.get('category') or '').strip().lower()
                    flat.append(d)
            return flat

        return to_flat_items(raw or [])

    # ----------------------------
    # Override Create
    # ----------------------------
    @api.model
    def create(self, vals):
        # First create catering order record
        catering_order = super().create(vals)

        # ✅ Create or update customer (res.partner)
        partner = self.env['res.partner'].search([('email', '=', catering_order.email)], limit=1)
        if partner:
            partner.write({
                'name': catering_order.customer_name,
                'phone': catering_order.phone,
                'street': catering_order.address,
            })
        else:
            partner = self.env['res.partner'].create({
                'name': catering_order.customer_name,
                'email': catering_order.email,
                'phone': catering_order.phone,
                'street': catering_order.address,
            })

        # ----------------------------
        # Create Sale Order
        # ----------------------------
        service_label = dict(self._fields['service_type'].selection).get(catering_order.service_type, '')

        sale_order = self.env['sale.order'].create({
            'partner_id': partner.id,
            'origin': 'Catering Service',
            'validity_date': catering_order.event_date,
            'note': (
                "Catering service quotation request from website\n"
                f"Service Type: {service_label}\n"
                f"Phone: {catering_order.phone or ''}\n"
                f"Email: {catering_order.email or ''}\n"
                f"Address: {catering_order.address or ''}"
            ),
        })

        # ----------------------------
        # Normalize items
        # ----------------------------
        raw = []
        if catering_order.menu_selection:
            try:
                raw = json.loads(catering_order.menu_selection)
            except Exception:
                raw = []
        items = self._normalize_items(raw)

        # ----------------------------
        # Add Sale Order Lines grouped by Category (Option 1: dynamic categories)
        # ----------------------------
        category_order = ['welcome', 'starter', 'main', 'biryani', 'dessert', 'leaf']
        pretty = {
            'welcome': 'Welcome Drinks',
            'starter': 'Starter Course',
            'main': 'Main Course',
            'biryani': 'Biryani & Specials',
            'dessert': 'Desserts',
            'leaf': 'Leaf-End Items',
        }

        # Build dynamic groups from items (preserve first-seen order)
        grouped_dynamic = {}
        appearance_order = []
        for it in items:
            cat_key = (it.get('category') or '').strip().lower() or 'other'
            if cat_key not in grouped_dynamic:
                grouped_dynamic[cat_key] = []
                appearance_order.append(cat_key)
            grouped_dynamic[cat_key].append(it)

        # Build ordered keys: known categories (in category_order) first if present, then others in appearance order
        ordered_keys = []
        for k in category_order:
            if k in grouped_dynamic:
                ordered_keys.append(k)
        for k in appearance_order:
            if k not in ordered_keys:
                ordered_keys.append(k)

        line_seq = 10

        def add_section(name):
            nonlocal line_seq
            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'name': name,
                'display_type': 'line_section',
                'sequence': line_seq,
            })
            line_seq += 10

        # Create section + product lines per ordered key
        for cat_key in ordered_keys:
            cat_items = grouped_dynamic.get(cat_key) or []
            if not cat_items:
                continue
            # choose section label: pretty mapping for known keys, otherwise title-case the category string
            section_label = pretty.get(cat_key) if cat_key in pretty else (cat_key.title() if cat_key else 'Other')
            add_section(section_label)
            for item in cat_items:
                price = float(item.get('price', 0.0))
                item_qty = float(item.get('qty', 1.0))
                total_qty = item_qty * catering_order.quantity

                product = self.env['product.product'].search([('name', '=', item.get('name'))], limit=1)
                if not product:
                    product_template = self.env['product.template'].create({
                        'name': item.get('name'),
                        'list_price': price,
                        'type': 'consu',
                        'sale_ok': True,
                    })
                    product = product_template.product_variant_id

                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': product.id,
                    'product_uom_qty': total_qty,
                    'price_unit': price,
                    'sequence': line_seq,
                })
                line_seq += 10

        # ----------------------------
        # Service charges based on service_type
        # ----------------------------
        # For 'delivery' and 'delivery_suppliers' we add a "Service Charges" section once.
        needs_transport = catering_order.service_type in ('delivery', 'delivery_suppliers')
        needs_suppliers = catering_order.service_type == 'delivery_suppliers'

        if needs_transport or needs_suppliers:
            add_section('Service Charges')

            if needs_suppliers:
                count = max(0, int(catering_order.suppliers_count or 0))
                amount = 500.0 * count
                if amount > 0:
                    prod_sup = self._get_or_create_product('Supplier Charge', ptype='service')
                    self.env['sale.order.line'].create({
                        'order_id': sale_order.id,
                        'product_id': prod_sup.id,
                        'name': f"Supplier Charge (₹500 × {count})",
                        'product_uom_qty': 1,
                        'price_unit': amount,
                        'sequence': line_seq,
                    })
                    line_seq += 10

            if needs_transport:
                prod_tr = self._get_or_create_product('Transportation Charge', ptype='service')
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': prod_tr.id,
                    'name': "Transportation Charge",
                    'product_uom_qty': 1,
                    'price_unit': 200.0,
                    'sequence': line_seq,
                })
                line_seq += 10

        # ----------------------------
        # Add Info Note Line (quantity)
        # ----------------------------
        if catering_order.quantity > 0:
            self.env['sale.order.line'].create({
                'order_id': sale_order.id,
                'name': f'Catering Quantity x{catering_order.quantity}',
                'display_type': 'line_note',
                'sequence': line_seq,
            })
            line_seq += 10

        # ----------------------------
        # Link Sale Order & Set State
        # ----------------------------
        catering_order.sale_order_id = sale_order.id
        catering_order.state = 'quotation'

        # ----------------------------
        # Optional: Auto-send Quotation Email
        # ----------------------------
        template = self.env.ref('sale.email_template_edi_sale', raise_if_not_found=False)
        if template:
            template.send_mail(sale_order.id, force_send=True)

        return catering_order
