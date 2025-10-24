from odoo import api, fields, models

class HrAttendance(models.Model):
    _inherit = "hr.attendance"

    zkuser = fields.Integer(string="User ID")
    zkusername = fields.Char(string="User Name")
    zk_device_id = fields.Many2one(comodel_name='vitouzkf.set.device', string='Device ID',  store=True)
    zk_devicename = fields.Char(related='zk_device_id.name', string="Device Name")
    zk_device_ip = fields.Char(related='zk_device_id.device_ip', string="Device IP")

    zk_staff_status = fields.Selection(
        related='employee_id.status_vitouzk', string='Staff Status', default='Active', store=True
    )
    zk_state_att = fields.Selection(
            string="State Att",
            selection=[
                ('posted', 'Posted'),
                ('download', 'Download'),
            ], default="download"
        )

