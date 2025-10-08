/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.table_reservation = publicWidget.Widget.extend({
    selector: '.swa_container',
    events: {
        'change #floors_rest': '_onFloorChange',
        'change #date_booking_input': '_onDateChange', // watch for date change
    },

    /**
     * To get all tables belongs to the floor
     **/
    _onFloorChange: function (ev) {
        var floors = this.$el.find("#floors_rest")[0].value;
        var date = this.$el.find("#date_booking").text().trim();
        var start = this.$el.find("#booking_start").text();

        if (document.getElementById('count_table')) {
            document.getElementById('count_table').innerText = 0;
        }
        if (document.getElementById('total_amount')) {
            document.getElementById('total_amount').innerText = 0;
        }

        var self = this;
        if (floors && date && start) {
            jsonrpc("/restaurant/floors/tables", {
                'floors_id': floors,
                'date': date,
                'start': start,
            }).then(function (data) {
                if (floors == 0) {
                    self.$el.find('#table_container_row').empty();
                    self.$el.find('#info').hide();
                } else {
                    self.$el.find('#table_container_row').empty();
                    self.$el.find('#info').show();
                    for (let i in data) {
                        let amount = '';
                        if (data[i]['rate'] != 0) {
                            amount = '<br/><span><i class="fa fa-money"></i></span><span id="rate">' +
                                data[i]['rate'] + '</span>/Slot';
                        }
                        self.$el.find('#table_container_row').append(
                            '<div id="' + data[i]['id'] +
                            '" class="card card_table col-sm-2" style="background-color:#96ccd5;padding:0;margin:5px;width:250px;">' +
                            '<div class="card-body"><b>' + data[i]['name'] +
                            '</b><br/><br/><br/><span><i class="fa fa-user-o" aria-hidden="true"></i> ' + data[i]['seats'] +
                            '</span>' + amount + '</div></div><br/>'
                        );
                    }
                }
            });
        }
    },

    /**
     * On Date Change: Filter available time slots to skip past times if today
     **/
    _onDateChange: function (ev) {
        const dateInput = ev.currentTarget;
        const selectedDate = new Date(dateInput.value);
        const startTimeSelect = this.el.querySelector("#booking_start");
        const endTimeSelect = this.el.querySelector("#booking_end");

        if (!startTimeSelect || !endTimeSelect) return;

        startTimeSelect.innerHTML = "";
        endTimeSelect.innerHTML = "";

        const now = new Date();
        const isToday = selectedDate.toDateString() === now.toDateString();

        let startHour = 0;
        let startMinute = 0;

        if (isToday) {
            startHour = now.getHours();
            if (now.getMinutes() < 30) {
                startMinute = 30;
            } else {
                startMinute = 0;
                startHour += 1;
            }
        }

        for (let hour = startHour; hour < 24; hour++) {
            for (let minute of [0, 30]) {
                if (isToday && hour === startHour && minute < startMinute) {
                    continue;
                }
                const timeStr = String(hour).padStart(2, "0") + ":" + String(minute).padStart(2, "0");
                startTimeSelect.add(new Option(timeStr, timeStr));
                endTimeSelect.add(new Option(timeStr, timeStr));
            }
        }
    },
});
