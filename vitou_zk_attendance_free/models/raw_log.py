from odoo import models, fields, api


class VitouzkRawLog(models.Model):
    _name = 'vitouzkf.raw.log'
    _description = 'Vitouzk Raw Incoming Log'

    source = fields.Char(string='Source', help='Remote IP or source identifier')
    path = fields.Char(string='Path')
    params = fields.Text(string='Query Params')
    payload = fields.Text(string='Payload')
    created_at = fields.Datetime(string='Created At', default=lambda self: fields.Datetime.now())

    @api.model
    def create_from_request(self, request):
        """Helper to create a raw log from an odoo request object."""
        try:
            source = request.httprequest.remote_addr
        except Exception:
            source = False
        try:
            params = dict(request.httprequest.args) if request.httprequest.args else {}
        except Exception:
            params = {}
        try:
            data = request.httprequest.data.decode('utf-8') if request.httprequest.data else ''
        except Exception:
            data = ''
        return self.create({
            'source': source,
            'path': request.httprequest.path,
            'params': str(params),
            'payload': data,
        })
