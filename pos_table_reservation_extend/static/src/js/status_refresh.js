(function () {
    'use strict';

    function fetchStatus(floorId) {
        var url = '/pos_manager/dashboard/status';
        if (floorId && floorId !== '0') {
            url += '?floor_id=' + encodeURIComponent(floorId);
        }
        return fetch(url, {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Accept': 'application/json'
            }
        }).then(function (r) {
            if (!r.ok) throw new Error('HTTP ' + r.status);
            return r.json();
        });
    }

    function updateUI(statusData) {
        Object.keys(statusData).forEach(function (tableId) {
            var el = document.querySelector('[data-table-id="' + tableId + '"]');
            if (!el) return;
            el.classList.remove('status-green','status-red','status-yellow');
            el.classList.add('status-' + (statusData[tableId].status || 'green'));
            var statusLabel = el.querySelector('.table-status');
            if (statusLabel) {
                var map = {'green':'Available','red':'Occupied','yellow':'Future Booking'};
                statusLabel.textContent = map[statusData[tableId].status] || 'Available';
            }
        });
    }

    function refreshForFloor(floorId) {
        fetchStatus(floorId).then(function (data) {
            updateUI(data);
        }).catch(function (err) {
            console.warn('Failed to refresh POS table statuses', err);
        });
    }

    function bindTableClicks() {
        document.addEventListener('click', function(e) {
            var box = e.target.closest('.table-box');
            if (!box) return;
            var tableName = box.querySelector('.table-name').textContent;
            var tableStatus = box.querySelector('.table-status').textContent;
            document.querySelector('#modal-body-content').textContent = 
                `Table: ${tableName}\nStatus: ${tableStatus}`;
            var modal = new bootstrap.Modal(document.getElementById('posDashboardModal'));
            modal.show();
        });
    }

    document.addEventListener('DOMContentLoaded', function () {
        var select = document.getElementById('floor_select');
        if (!select) return;
        function doRefresh() {
            var val = select.value || '0';
            refreshForFloor(val);
        }
        select.addEventListener('change', doRefresh);
        doRefresh(); // initial
        setInterval(doRefresh, 20000); // poll each 20s
        bindTableClicks();
    });
})();
