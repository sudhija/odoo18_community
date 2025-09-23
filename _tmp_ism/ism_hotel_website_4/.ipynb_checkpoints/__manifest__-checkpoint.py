{
    'name': 'ISM hotel 4 website ',
    'version': '17.0.1.0.1',
    'summary': 'Website frontend for ISM Hotel with validations, categories, gallery, and payment methods display',
    'depends': ['website', 'portal', 'sale_management', 'account', 'ism_hotel', 'payment'],
    'data': [
        'security/ir.model.access.csv',
        'security/hotel_room_security.xml',
        'views/backend_inherit_views.xml',
        'views/backend_menus.xml',
        'views/website_menu.xml',                 # <-- FIXED filename
        'views/website_hotel_home.xml',
        'views/website_hotel_room_detail.xml',     # keep only this room detail template
        'views/website_templates.xml',             # contains checkout + thanks
        'data/cron_jobs.xml',
    ],
    'installable': True,
    'application': False,
}
