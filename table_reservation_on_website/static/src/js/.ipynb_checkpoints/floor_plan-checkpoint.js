odoo.define('restaurant_reservation.floor_plan', function (require) {
    "use strict";

    const publicWidget = require('web.public.widget');

    publicWidget.registry.TableFloorPlan = publicWidget.Widget.extend({
        selector: '.floor-plan-container',
        events: {
            'click .table-block': '_onTableClick',
        },

        start: function () {
            return this._super.apply(this, arguments).then(() => {
                this._colorizeTables();
            });
        },

        _onTableClick: function (ev) {
            const $target = $(ev.currentTarget);
            const tableId = $target.data('table-id');
            alert('You clicked table ID: ' + tableId);
        },

        _colorizeTables: function () {
            this.$('.table-block').each(function () {
                const $table = $(this);
                const occupied = $table.data('occupied');
                if (occupied) {
                    $table.css('background-color', '#FF4D4D');  // red
                } else {
                    $table.css('background-color', '#4CAF50');  // green
                }
            });
        },
    });

    return publicWidget.registry.TableFloorPlan;
});
