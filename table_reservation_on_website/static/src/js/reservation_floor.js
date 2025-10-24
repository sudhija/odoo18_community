/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";

let booked_table = [];

publicWidget.registry.table_reservation_floor = publicWidget.Widget.extend({
    selector: '#tableContainer',
    events: {
        'click .card_table': '_onTableClick',
    },

    /**
     * Select table for reservation
     **/
    _onTableClick: function (ev) {
        this.$el.find('.submit_button').prop('disabled', false);

        // ✅ Use the event from the parameter (was missing before)
        const current_div_id = ev.currentTarget;
        const rateElement = current_div_id.querySelector('#rate');
        const countElement = this.$el.find('#count_table')[0];
        const amountElement = this.$el.find('#total_amount')[0];
        const bookedElement = this.$el.find('#tables_input')[0];

        const rate = rateElement ? Number(rateElement.innerText) : 0;

        // ✅ If already selected → deselect
        if (current_div_id.style.backgroundColor === 'green') {
            const tableId = Number(current_div_id.id);
            const index = booked_table.indexOf(tableId);
            if (index !== -1) {
                booked_table.splice(index, 1);
            }
            current_div_id.style.backgroundColor = '#96ccd5';

            if (countElement) {
                const countText = countElement.innerText.trim();
                const count = countText !== '' ? Number(countText) : 0;
                countElement.innerText = count > 0 ? count - 1 : 0;
            }

            if (amountElement) {
                amountElement.innerText = Number(amountElement.innerText) - rate;
            }
        }
        // ✅ If not selected → select
        else {
            current_div_id.style.backgroundColor = 'green';
            if (countElement) {
                const countText = countElement.innerText.trim();
                const count = countText !== '' ? Number(countText) : 0;
                countElement.innerText = count + 1;
            }
            booked_table.push(Number(current_div_id.id));

            if (amountElement) {
                const currentAmount = amountElement.innerText ? Number(amountElement.innerText) : 0;
                amountElement.innerText = currentAmount + rate;
            }
        }

        if (bookedElement) {
            bookedElement.value = booked_table;
        }

        // ✅ Toggle submit button
        const countTableEl = this.$el.find('#count_table')[0];
        if (countTableEl) {
            const currentCount = Number(countTableEl.innerText.trim());
            this.$el.find('.submit_button').prop('disabled', currentCount === 0);
        }
    },
});
