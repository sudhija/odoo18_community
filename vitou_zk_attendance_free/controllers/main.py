import logging
import logging
from odoo import http, SUPERUSER_ID
from odoo.http import request

logger = logging.getLogger(__name__)


class ZkController(http.Controller):

    # Accept both POST and GET (some devices send GET) and also accept a trailing slash.
    @http.route(['/iclock/cdata', '/iclock/cdata/'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
    def receivedata(self, **kwargs):
        # SN and other params may be sent as query params; data payload in request body.
        sn = kwargs.get('SN') or request.httprequest.args.get('SN')
        try:
            data = request.httprequest.data.decode('utf-8') if request.httprequest.data else ''
        except Exception:
            data = ''

        logger.info(f"Received data from device {sn}: payload_len={len(data)} args={dict(request.httprequest.args)}")

        # Use a superuser env for DB operations (auth='none' routes can have an empty env.user)
        su_env = request.env(user=SUPERUSER_ID)

        # Persist raw incoming request for debugging (don't fail the whole request if this fails)
        try:
            su_env['vitouzkf.raw.log'].create_from_request(request)
        except Exception:
            logger.exception("Failed to persist raw log")

        # Some devices send data as query param 'data' or via GET; try to extract.
        if not data:
            data = kwargs.get('data') or request.httprequest.args.get('data') or ''

        # Determine table param (ATTLOG/OPERLOG)
        table = (kwargs.get('table') or request.httprequest.args.get('table') or '').upper()

        try:
            if table == 'ATTLOG':
                # Expected format per line: ATTLOG <userid> <YYYY-MM-DD> <HH:MM:SS>
                for line in data.splitlines():
                    if not line.strip():
                        continue
                    parts = line.strip().split()
                    if not parts or len(parts) < 4:
                        logger.debug(f"Skipping malformed ATTLOG line from {sn}: '{line}'")
                        continue
                    # parts[0] == 'ATTLOG'
                    userid = parts[1]
                    datepart = parts[2]
                    timepart = parts[3]
                    timestamp = f"{datepart} {timepart}"

                    employee = su_env['hr.employee'].search([('barcode', '=', userid)], limit=1)
                    if not employee:
                        logger.warning(f"No employee found for device user id {userid}")
                        continue

                    # Dedupe: avoid creating identical attendance with same check_in
                    exists = su_env['hr.attendance'].search([
                        ('employee_id', '=', employee.id),
                        ('check_in', '=', timestamp),
                    ], limit=1)
                    if exists:
                        logger.info(f"Duplicate attendance skipped for {employee.name} at {timestamp}")
                        continue

                    try:
                        su_env['hr.attendance'].create({
                            'employee_id': employee.id,
                            'check_in': timestamp,
                        })
                        logger.info(f"Attendance created for {employee.name} at {timestamp}")
                    except Exception:
                        logger.exception(f"Failed to create attendance for {userid} at {timestamp}")
            else:
                # Fallback: try to parse generic ATTLOG-like lines
                for line in data.splitlines():
                    if not line.strip():
                        continue
                    parts = line.strip().split()
                    if parts and len(parts) >= 3:
                        # attempt old behavior: userid date time
                        userid, datepart, timepart = parts[:3]
                        timestamp = f"{datepart} {timepart}"
                        employee = su_env['hr.employee'].search([('barcode', '=', userid)], limit=1)
                        if employee:
                            exists = su_env['hr.attendance'].search([
                                ('employee_id', '=', employee.id),
                                ('check_in', '=', timestamp),
                            ], limit=1)
                            if not exists:
                                try:
                                    su_env['hr.attendance'].create({
                                        'employee_id': employee.id,
                                        'check_in': timestamp,
                                    })
                                    logger.info(f"Attendance created for {employee.name} at {timestamp}")
                                except Exception:
                                    logger.exception(f"Failed to create attendance for {userid} at {timestamp}")
                        else:
                            logger.debug(f"No employee found for fallback id {userid}")
        except Exception:
            import logging
            from odoo import http, SUPERUSER_ID
            from odoo.http import request

            logger = logging.getLogger(__name__)


            class ZkController(http.Controller):

                @http.route(['/iclock/cdata', '/iclock/cdata/'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
                def receivedata(self, **kwargs):
                    sn = kwargs.get('SN') or request.httprequest.args.get('SN')
                    try:
                        data = request.httprequest.data.decode('utf-8') if request.httprequest.data else ''
                    except Exception:
                        data = ''

                    logger.info('Received data from device %s: payload_len=%d args=%s', sn, len(data), dict(request.httprequest.args))

                    su_env = request.env(user=SUPERUSER_ID)

                    try:
                        su_env['vitouzkf.raw.log'].create_from_request(request)
                    except Exception:
                        logger.exception('Failed to persist raw log')

                    if not data:
                        data = kwargs.get('data') or request.httprequest.args.get('data') or ''

                    table = (kwargs.get('table') or request.httprequest.args.get('table') or '').upper()

                    try:
                        if table == 'ATTLOG':
                            for line in data.splitlines():
                                if not line.strip():
                                    continue
                                parts = line.strip().split()
                                if not parts or len(parts) < 4:
                                    logger.debug('Skipping malformed ATTLOG line from %s: %s', sn, line)
                                    continue
                                userid = parts[1]
                                datepart = parts[2]
                                timepart = parts[3]
                                timestamp = f"{datepart} {timepart}"

                                employee = su_env['hr.employee'].search([('barcode', '=', userid)], limit=1)
                                if not employee:
                                    logger.warning('No employee found for device user id %s', userid)
                                    continue

                                exists = su_env['hr.attendance'].search([('employee_id', '=', employee.id), ('check_in', '=', timestamp)], limit=1)
                                if exists:
                                    logger.info('Duplicate attendance skipped for %s at %s', employee.name, timestamp)
                                    continue

                                try:
                                    su_env['hr.attendance'].create({'employee_id': employee.id, 'check_in': timestamp})
                                    logger.info('Attendance created for %s at %s', employee.name, timestamp)
                                except Exception:
                                    logger.exception('Failed to create attendance for %s at %s', userid, timestamp)
                        else:
                            for line in data.splitlines():
                                if not line.strip():
                                    continue
                                parts = line.strip().split()
                                if parts and len(parts) >= 3:
                                    userid, datepart, timepart = parts[:3]
                                    timestamp = f"{datepart} {timepart}"
                                    employee = su_env['hr.employee'].search([('barcode', '=', userid)], limit=1)
                                    if employee:
                                        exists = su_env['hr.attendance'].search([('employee_id', '=', employee.id), ('check_in', '=', timestamp)], limit=1)
                                        if not exists:
                                            try:
                                                su_env['hr.attendance'].create({'employee_id': employee.id, 'check_in': timestamp})
                                                logger.info('Attendance created for %s at %s', employee.name, timestamp)
                                            except Exception:
                                                logger.exception('Failed to create attendance for %s at %s', userid, timestamp)
                                    else:
                                        logger.debug('No employee found for fallback id %s', userid)
                    except Exception:
                        logger.exception('Unhandled error while processing device payload')

                    return request.make_response('OK', [('Content-Type', 'text/plain')])

                @http.route(['/iclock/getrequest', '/iclock/getrequest/'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
                def getrequest(self, **kwargs):
                    sn = kwargs.get('SN') or request.httprequest.args.get('SN')
                    logger.info('Device %s requested command check', sn)
                    return request.make_response('OK', [('Content-Type', 'text/plain')])

                @http.route(['/iclock', '/iclock/<path:sub>'], type='http', auth='none', methods=['GET', 'POST'], csrf=False)
                def iclock_catchall(self, sub=None, **kwargs):
                    req = request.httprequest
                    args = dict(req.args) if req.args else {}
                    logger.info('ICLOCK CATCHALL: sub=%s method=%s remote=%s args=%s content_len=%d', sub, req.method, req.remote_addr, args, len(req.data or b''))
                    return request.make_response('OK', [('Content-Type', 'text/plain')])
