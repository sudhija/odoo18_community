{
    'name': 'Website Catering Service',
    'version': '1.0',
    'category': 'Website',
    'summary': 'Custom Catering Page with Menu Selection',
    'depends': ['base','website', 'website_sale'],
    'data': [        'report/report_saleorder_catering_align.xml',
        'security/ir.model.access.csv',
        'views/catering_category_views.xml',
        'views/menu.xml',
        'views/catering_template.xml',
        'views/catering_customer_form.xml',
        'views/catering_order_views.xml',
        'views/thank_you_template.xml',
        'views/quotation_template.xml',
        
        # 'data/email_template.xml', 
    ],
    'installable': True,
    'application': False
}
