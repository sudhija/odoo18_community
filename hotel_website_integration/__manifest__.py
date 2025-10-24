{
    'name': 'Hotel Website Integration',
    'version': '18.0.1.0.5',
    'depends': ['website', 'portal', 'website_sale', 'sale_management', 'account', 'payment', 'hotel_management_odoo'],
    'data': [
        'security/ir.model.access.csv',
        'security/hotel_room_security.xml',
        'views/backend_inherit_views.xml',
        'views/backend_menus.xml',
        'views/website_menu.xml',                 # <-- FIXED filename
        'views/website_hotel_home.xml',
        'views/website_hotel_room_detail.xml',     # keep only this room detail template
        'views/website_templates.xml',              # contains checkout + thanks
        'data/cron_jobs.xml',  # temporarily disabled until cron method is implemented  
    ],  
    'assets': {
        'web.assets_backend': [
            'hotel_website_integration/static/src/js/hotel_form.js',
            #'hotel_website_integration/static/src/xml/hotel_form.xml',
        ],
    },
    'installable': True,
    'application': False,
    #'post_init_hook': 'post_init_hook',
}
