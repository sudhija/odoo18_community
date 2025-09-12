{
	'name': 'Website Sale MQTT Order',
	'version': '18.0.1.0',
	'summary': 'Publish orders to MQTT and track status on website',
	'category': 'Website/Commerce',
	'license': 'LGPL-3',
	'depends': ['website_sale', 'portal', 'mail', 'base', 'base_setup', 'mqtt_integration'],
	'data': [
		'views/res_config_settings_views.xml',
		'security/ir.model.access.csv',
		'views/portal_templates.xml',
		'data/cron.xml'
	],
	'installable': True,
	'application': False
}
