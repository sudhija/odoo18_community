{
    'name': 'POS Table Reservation - Extended',
    'version': '1.0.0',
    'summary': 'Responsive floor plan, color coded table statuses and POS Manager dashboard for Cybrosys Table Reservation',
    'description': 'Extends the table_reservation_on_website module to add responsive UI, color coding (occupied/free/future), and a website dashboard for POS managers.',
    'category': 'Point of Sale',
    'author': 'Swaroop C',
    'website': 'https://www.emidastec.in',
    'license': 'LGPL-3',
    'depends': [
        'pos_restaurant',
        'table_reservation_on_website',
        'website',
        'base'
    ],
    'data': [
        'views/pos_dashboard_templates.xml'
        # 'views/pos_dashboard_menu.xml'
    ],
    # 'assets': {
    #     'web.assets_frontend': [
    #         'pos_table_reservation_extend/static/src/css/pos_dashboard.css',
    #         'pos_table_reservation_extend/static/src/css/style.css',
    #         'pos_table_reservation_extend/static/src/js/status_refresh.js'
    #     ],
    #     'web.assets_backend': []
    # },
    'installable': True,
    'application': False,
    'auto_install': False
}
