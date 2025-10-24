# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json

class POSDashboard(http.Controller):

    @http.route('/pos_manager/dashboard', type='http', auth='user', website=True)
    def pos_manager_dashboard(self, **kw):
        """Website page for POS manager to view and manage floor plans.
           Accessible only for internal users."""
        
        # Get current user
        user = request.env.user
        
        # Check if user is internal
        if user.has_group('base.group_user'):  # Internal user group
            floors = request.env['restaurant.floor'].sudo().search([])
            return request.render(
                'pos_table_reservation_extend.pos_dashboard_template', 
                {'floors': floors}
            )
        else:
            # Optionally redirect or raise error
            return request.redirect('/web/login')  # or AccessDenied

    @http.route('/pos_manager/dashboard/status', type='http', auth='user', website=True)
    def pos_manager_status(self, floor_id=None, **kw):
        """Return JSON mapping of table_id -> color_status for a floor.
        This is an HTTP JSON endpoint so it can be fetched directly (GET/POST).
        """
        # prefer explicit parameter from query or body
        if not floor_id:
            floor_id = request.params.get('floor_id') or request.httprequest.args.get('floor_id')

        domain = []
        if floor_id and str(floor_id) != '0':
            try:
                domain = [('floor_id', '=', int(floor_id))]
            except Exception:
                domain = []

        tables = request.env['restaurant.table'].sudo().search(domain)
        data = {}
        for t in tables:
            # `color_status` is compute (store=False) — reading it triggers compute
            data[str(t.id)] = {
                'name': t.name,
                'status': t.color_status or 'green',
            }
        return request.make_response(json.dumps(data), headers=[('Content-Type', 'application/json; charset=utf-8')])
