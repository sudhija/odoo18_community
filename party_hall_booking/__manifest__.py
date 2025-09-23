{
    "name": "Party Hall Booking",
    "version": "17.1.0",
    "summary": "Website listing + hall detail + availability check + booking with duplicate prevention",
    "category": "Website",
    "depends": ["base","website"],
    "data": [
        "security/ir.model.access.csv",
        "views/menu.xml",
        "views/party_hall_views.xml",
        "views/party_hall_booking_views.xml",
        "views/booking_templates.xml",
        "views/website_menu.xml"
    ],
    "assets": {
        "website.assets_frontend": [
            "party_hall_booking_odoo18/static/src/js/booking.js",
            "party_hall_booking_odoo18/static/src/css/booking.css"
        ]
    },
    "installable": True,
    "application": True
}