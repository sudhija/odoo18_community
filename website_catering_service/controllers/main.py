from odoo import http
from odoo.http import request
import json


class CateringController(http.Controller):

    # ----------------------------
    # Catering Menu Page
    # ----------------------------
    @http.route(['/catering'], type='http', auth='public', website=True)
    def catering_page(self, **kwargs):
        selected_items = request.session.get('selected_items', {})

        # default empty recordset for product.template
        Product = request.env['product.template'].sudo()
        welcome_items = Product.browse([])  # empty
        starter_items = Product.browse([])
        main_items = Product.browse([])
        biryani_items = Product.browse([])
        dessert_items = Product.browse([])
        leaf_items = Product.browse([])

        # Fetch categories dynamically (published ones)
        categories = request.env['catering.category'].sudo().search(
            [('website_published', '=', True)],
            order='sequence asc, name asc'
        )

        # Fill the template variables by matching category names (keeps your frontend unchanged)
        for cat in categories:
            # filter products to those that are saleable and published on website
            prods = cat.product_ids.filtered(lambda p: p.sale_ok and p.website_published)
            name = (cat.name or '').strip().lower()

            # Flexible matching to handle small name differences
            if name in ('welcome drinks', 'welcome', 'welcome drink', 'welcome drinks '):
                welcome_items = prods
            elif name in ('starter', 'starter course', 'starters'):
                starter_items = prods
            elif name in ('main course', 'main', 'main courses'):
                main_items = prods
            elif 'biryani' in name or 'special' in name:
                biryani_items = prods
            elif name in ('dessert', 'desserts', 'sweet'):
                dessert_items = prods
            elif 'leaf' in name or 'leaf-end' in name or 'leaf end' in name:
                leaf_items = prods
            else:
                # unknown categories left as-is; template receives full `categories` recordset below
                pass

        # include categories in context so the template's dynamic branch can render any new categories
        return request.render('website_catering_service.catering_page_template', {
            'welcome_items': welcome_items,
            'starter_items': starter_items,
            'main_items': main_items,
            'biryani_items': biryani_items,
            'dessert_items': dessert_items,
            'leaf_items': leaf_items,
            'categories': categories,
            'selected_items': selected_items,
        })

    # ----------------------------
    # Save Selected Items in Session
    # ----------------------------
    @http.route('/catering/set-selected-items', type='json', auth='public', website=True)
    def set_selected_items(self, **post):
        request.session['selected_items'] = post
        request.session.modified = True
        return {'status': 'ok'}

    # ----------------------------
    # Save Total Amount in Session
    # ----------------------------
    @http.route('/catering/set-total', type='json', auth='public', website=True)
    def set_total_amount(self, total_amount):
        try:
            request.session['total_amount'] = float(total_amount)
        except Exception:
            request.session['total_amount'] = 0.0
        request.session.modified = True
        return {'status': 'ok'}

    # ----------------------------
    # Customer Details Form Page
    # ----------------------------
    @http.route(['/catering/customer-details'], type='http', auth='public', website=True, methods=['GET'])
    def catering_customer_details(self, **kwargs):
        selected_items = request.session.get('selected_items', {})
        total_amount = request.session.get('total_amount', 0.0)

        service_types = [
            ('takeaway', 'Take Away'),
            ('delivery', 'Delivery & Transportation'),
            ('delivery_suppliers', 'Delivery & Transportation & Suppliers'),
        ]

        return request.render('website_catering_service.catering_customer_form_template', {
            'selected_items': selected_items,
            'total_amount': total_amount,
            'service_types': service_types,
        })

    # ----------------------------
    # Handle Form Submit → Create Catering Order & Sale Order
    # ----------------------------
    @http.route('/catering/customer/submit', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def submit_catering_order(self, **post):
        # Parse suppliers_count safely (optional unless delivery_suppliers)
        try:
            suppliers_count = int(post.get('suppliers_count') or 0)
        except Exception:
            suppliers_count = 0

        catering_vals = {
            'customer_name': post.get('customer_name'),
            'email': post.get('email'),
            'phone': post.get('phone'),
            'address': post.get('address'),
            'event_date': post.get('event_date'),
            'service_type': post.get('service_type'),
            'suppliers_count': suppliers_count,
            'menu_selection': post.get('menu_selection'),
            'base_total': float(post.get('base_total', 0.0)),
            'quantity': int(post.get('quantity', 1)),
        }
        catering_rec = request.env['catering.order'].sudo().create(catering_vals)

        # ----------------------------
        # Sale Order PDF Download
        # ----------------------------
        sale_order = catering_rec.sudo().sale_order_id
        if not sale_order:
            return request.render('website_catering_service.thank_you_template')

        # clear session
        request.session.pop('selected_items', None)
        request.session.pop('total_amount', None)
        request.session.modified = True

        report_ref = "sale.action_report_saleorder"
        pdf_content, _ = request.env["ir.actions.report"]._render_qweb_pdf(
            report_ref, [sale_order.id]
        )
        return request.make_response(
            pdf_content,
            headers=[
                ('Content-Type', 'application/pdf'),
                ('Content-Disposition', f'attachment; filename="Quotation-{sale_order.name}.pdf"')
            ]
        )

    # ----------------------------
    # Thank You Page
    # ----------------------------
    @http.route('/catering/thank-you', type='http', auth='public', website=True)
    def catering_thank_you(self, **kwargs):
        return request.render('website_catering_service.thank_you_template')

    # ----------------------------
    # Redirect from Button (Optional)
    # ----------------------------
    @http.route('/catering/get-quotation', type='http', auth='public', website=True, methods=['POST'], csrf=False)
    def catering_get_quotation(self, **post):
        return request.redirect('/catering/customer-details')
