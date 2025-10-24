# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#    Copyright (C) 2024-TODAY Cybrosys Technologies
#    Author: Aysha Shalin (odoo@cybrosys.com)
#
###############################################################################

{
    'name': 'Table Reservation On POS And Website',
    'version': '18.0.1.0',
    'category': 'eCommerce,Point of Sale',
    'summary': 'Reserve tables in POS from website with smart dashboard and auto-release',
    'description': """Enhances table reservation with real-time floor plan UI, 
    auto-release of tables post reservation, and POS manager dashboard.""",
    'author': 'Cybrosys Techno Solutions, Updated by You',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': [
        'pos_restaurant',
        'base',
        'website_sale',
        'sale_management',
        'website_event',  # ✅ Added to support event registrations properly
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/automatic_invoice.xml',
        'data/table_reservation_data.xml',
        'data/product_product_data.xml',
        'data/scheduled_action.xml',
        'views/table_reservation_templates.xml',
        'views/table_reservation_on_website_menus.xml',
        'views/restaurant_table_views.xml',
        'views/restaurant_floor_views.xml',
        'views/table_reservation_views.xml',  
        'views/sale_order_views.xml',
        'views/table_reserved_templates.xml',
        'views/res_config_settings_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'table_reservation_on_website/static/src/app/screens/floor_screen/floor_screen.js',
            'table_reservation_on_website/static/src/app/screens/floor_screen/floor_screen.xml',
            'table_reservation_on_website/static/src/app/screens/product_screen/product_screen.js',
            'table_reservation_on_website/static/src/app/screens/reservation_screen/reservation_screen.js',
            'table_reservation_on_website/static/src/app/screens/reservation_screen/reservation_screen.xml',
            'table_reservation_on_website/static/src/app/booking_popup/editBookingPopup.js',
            'table_reservation_on_website/static/src/app/booking_popup/editBookingPopup.xml',
            'table_reservation_on_website/static/src/app/booking_popup/createBookingPopup.js',
            'table_reservation_on_website/static/src/app/booking_popup/createBookingPopup.xml',
            'table_reservation_on_website/static/src/scss/style.css',
        ],
        'web.assets_frontend': [
            'table_reservation_on_website/static/src/js/table_reservation.js',
            'table_reservation_on_website/static/src/js/reservation.js',
            'table_reservation_on_website/static/src/js/reservation_floor.js',
            # 'table_reservation_on_website/static/src/js/floor_plan.js',
        ],
    },
    'images': ['static/description/banner.png'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}

