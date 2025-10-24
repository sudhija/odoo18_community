# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (C) 2024-TODAY,
#    Author: REAM Vitou (reamvitou@yahoo.com)
#    Tel: +855 17 82 66 82


###############################################################################

{
    'name': 'ZK-Biometric Device Integration',
    'version': '18.0.1.0.2',
    'category': 'Human Resources',
    'summary': "Integrating Biometric Device With HR Attendance (Face + Thumb)",
    'description': "Integrating Biometric Device With HR Attendance (Face + Thumb)",
    'author': 'V Technologies',
    'company': 'V Technologies',
    'maintainer': 'V Technologies',
    'website': 'https://apps.odoo.com/apps/modules/browse?search=vitou',
    'module_type': 'official',
    # 'price': '50',
    # 'currency': 'USD',
    'depends': ['base_setup', 'hr_attendance', 'hr'],

    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron.xml',

        # data
        'data/developer_default.xml',
        'data/paperformat_landscap.xml',

        # action
        'views/action/download_att.xml',
        'views/action/copy_att.xml',
        'views/action/done_att_fix.xml',
        'views/action/open_report_att_fix.xml',
        'views/action/open_help.xml',
        'views/action/download_att_flexible.xml',
        'views/action/done_att_flexible.xml',
        'views/action/open_report_att_flexible.xml',

        #report
        'report/att_fix_shift_report.xml',
        'report/att_flexible_shift_report.xml',

        # view

        'views/set_device.xml',
        'views/hr_employee_inherit_views.xml',
        'views/daily_attendance_views.xml',
        'views/daily_attendance_all_views.xml',
        'views/daily_attendance_all_flexible_views.xml',
        'views/zk_user.xml',
        'views/hs_shfits.xml',
        'views/hr_attendance_manager_inherit_views.xml',
        'views/hr_attendance_all_inherit_views.xml',

        'views/menu.xml',

    ],
    'license': 'AGPL-3',
    'installable': True,
    'images': ["static/description/banner.png"],
    'auto_install': False,
    'application': True,
    'sequence': 2
}
