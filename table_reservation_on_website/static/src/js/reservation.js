/** @odoo-module */
import publicWidget from "@web/legacy/js/public/public_widget";
import { jsonrpc } from "@web/core/network/rpc_service";

publicWidget.registry.reservation = publicWidget.Widget.extend({
    selector: '.container',
    events: {
        'change #date': '_onChangeDate',
        'change #start_time': '_onChangeTime',
        'change #end_time': '_onChangeTime',
        'change #tables_input': '_onTablesChanged',
        'click .close_btn_alert_modal': '_onClickCloseBtn',
        'click .close_btn_time_alert_modal': '_onClickCloseAlertBtn',
    },

    async start() {
        this.openingHour = null;
        this.closingHour = null;
        try {
            const result = await jsonrpc('/pos/get_opening_closing_hours', {});
            if (result && !result.error) {
                this.openingHour = result.opening_hour;   // expect "HH:MM AM/PM" or "HH:MM"
                this.closingHour = result.closing_hour;
            }
        } catch (e) {
            console.warn("Could not fetch opening hours", e);
        }

        this._syncHiddenInputsAndState();
        this._poller = setInterval(this._syncHiddenInputsAndState.bind(this), 400);
    },

    // convert "HH:MM" (24h) -> "hh:MM AM/PM" with leading zeros
    _to12Hour: function(timeStr){
        if (!timeStr) return '';
        timeStr = timeStr.toString().trim();

        // already AM/PM?
        if (/(AM|PM)$/i.test(timeStr)) {
            let m = timeStr.match(/(\d{1,2}):(\d{2})\s*(AM|PM)/i);
            if (m) {
                let hh = String(parseInt(m[1], 10)).padStart(2, '0');
                return `${hh}:${m[2]} ${m[3].toUpperCase()}`;
            }
            return timeStr;
        }

        // parse 24h HH:MM
        let m = timeStr.match(/^(\d{1,2}):(\d{2})$/);
        if (!m) return timeStr;
        let h = parseInt(m[1], 10);
        let min = m[2];
        let suffix = (h < 12) ? 'AM' : 'PM';
        let displayHour = h % 12;
        if (displayHour === 0) displayHour = 12;
        let hh = String(displayHour).padStart(2, '0');   // always 2 digits
        return `${hh}:${min} ${suffix}`;
    },

    // convert "hh:MM AM/PM" to minutes since midnight
    _toMinutes: function(timeStr){
        if (!timeStr) return null;
        timeStr = timeStr.trim();

        // 24h like "17:30"
        let m24 = timeStr.match(/^(\d{1,2}):(\d{2})$/);
        if (m24) {
            let h = parseInt(m24[1],10);
            let mm = parseInt(m24[2],10);
            return h * 60 + mm;
        }

        // AM/PM (supports 01,02,...09 hours also)
        let m = timeStr.match(/^0?(\d{1,2}):(\d{2})\s*(AM|PM)$/i);
        if (!m) return null;
        let h = parseInt(m[1],10);
        const mins = parseInt(m[2],10);
        const ampm = m[3].toUpperCase();
        if (ampm === 'AM' && h === 12) h = 0;
        if (ampm === 'PM' && h !== 12) h += 12;
        return h * 60 + mins;
    },

    _isPast: function(dateStr, timeStr){
        if (!dateStr || !timeStr) return false;
        try {
            const parts = dateStr.split('-'); // YYYY-MM-DD
            if (parts.length !== 3) return false;
            const y = parseInt(parts[0],10), mo = parseInt(parts[1],10)-1, d = parseInt(parts[2],10);
            const minutes = this._toMinutes(timeStr);
            if (minutes === null) return false;
            const hh = Math.floor(minutes / 60), mm = minutes % 60;
            const sel = new Date(y, mo, d, hh, mm, 0);
            const now = new Date();
            return sel.getTime() < now.getTime();
        } catch (e) {
            return false;
        }
    },

    _onChangeDate: function (ev) {
        try {
            const sel = this.$el.find("#date").val();
            if (!sel) {
                this.$el.find("#alert_modal").show();
                return;
            }
            const selectedDate = new Date(sel);
            const today = new Date();
            selectedDate.setHours(0,0,0,0);
            today.setHours(0,0,0,0);
            if (selectedDate < today) {
                this.$el.find("#alert_modal").show();
                this.$el.find("#date").val('');
            }
        } catch(e){
            console.error(e);
        }
        this._syncHiddenInputsAndState();
    },

    _onClickCloseBtn: function() {
        this.$el.find("#alert_modal").hide();
    },

    _onChangeTime: function () {
        const start_val = this.$el.find("#start_time").val();
        const end_val = this.$el.find("#end_time").val();
        const date_val = this.$el.find("#date").val();

        if (start_val) {
            const s12 = this._to12Hour(start_val);
            this.$el.find("#start_time").val(s12);
        }
        if (end_val) {
            const e12 = this._to12Hour(end_val);
            this.$el.find("#end_time").val(e12);
        }

        const sMin = this._toMinutes(this.$el.find("#start_time").val());
        const eMin = this._toMinutes(this.$el.find("#end_time").val());

        if (sMin !== null && eMin !== null) {
            if (sMin >= eMin) {
                this.$el.find("#time_alert_modal").show();
                this.$el.find("#start_time").val('');
                this.$el.find("#end_time").val('');
                this._syncHiddenInputsAndState();
                return;
            }
        }

        if (this.openingHour && this.closingHour) {
            const openMin = this._toMinutes(this.openingHour);
            const closeMin = this._toMinutes(this.closingHour);
            if (sMin !== null && (sMin < openMin || sMin > closeMin)) {
                this.$el.find("#open_hours_alert_modal").show();
                this.$el.find("#start_time").val('');
                this.$el.find("#end_time").val('');
                this._syncHiddenInputsAndState();
                return;
            }
            if (eMin !== null && (eMin < openMin || eMin > closeMin)) {
                this.$el.find("#open_hours_alert_modal").show();
                this.$el.find("#start_time").val('');
                this.$el.find("#end_time").val('');
                this._syncHiddenInputsAndState();
                return;
            }
        }

        if (date_val) {
            if (this._isPast(date_val, this.$el.find("#start_time").val())) {
                this.$el.find("#time_alert_modal").show();
                this.$el.find("#start_time").val('');
                this.$el.find("#end_time").val('');
                this._syncHiddenInputsAndState();
                return;
            }
        }

        this._syncHiddenInputsAndState();
    },

    _onTablesChanged: function() {
        this._syncHiddenInputsAndState();
    },

    _onClickCloseAlertBtn: function() {
        this.$el.find("#time_alert_modal").hide();
        this.$el.find("#open_hours_alert_modal").hide();
    },

    _syncHiddenInputsAndState: function() {
        try {
            const dateVal = this.$el.find("#date").val() || this.$el.find("#date_id").val() || '';
            let startVal = this.$el.find("#start_time").val() || this.$el.find("#start_id").val() || '';
            let endVal = this.$el.find("#end_time").val() || this.$el.find("#end_id").val() || '';
            let tablesVal = this.$el.find("#tables_input").val() || '';

            if (startVal) startVal = this._to12Hour(startVal);
            if (endVal) endVal = this._to12Hour(endVal);

            if (this.$el.find("#date_id").length) this.$el.find("#date_id").val(dateVal);
            if (this.$el.find("#start_id").length) this.$el.find("#start_id").val(startVal);
            if (this.$el.find("#end_id").length) this.$el.find("#end_id").val(endVal);
            if (this.$el.find("#tables_input").length) this.$el.find("#tables_input").val(tablesVal);

            const ready = dateVal && startVal && endVal && tablesVal &&
                (this._toMinutes(startVal) !== null) &&
                (this._toMinutes(endVal) !== null) &&
                (this._toMinutes(startVal) < this._toMinutes(endVal)) &&
                !this._isPast(dateVal, startVal);

            const $btn = this.$el.find("#booking_confirm_btn");
            if ($btn.length) {
                if (ready) {
                    $btn.prop('disabled', false);
                    $btn.removeAttr('disabled');
                } else {
                    $btn.prop('disabled', true);
                    $btn.attr('disabled', 'disabled');
                }
            }
        } catch (err) {
            console.error("syncHiddenInputsAndState error:", err);
        }
    },

    destroy: function () {
        clearInterval(this._poller);
        return this._super.apply(this, arguments);
    }

    events: {
    // ... existing events ...
    'click #booking_confirm_btn': '_onClickConfirmBtn',
},

    _onClickConfirmBtn: function (ev) {
        const isPublic = odoo.session_info.user_id === false;
        if (isPublic) {
            ev.preventDefault();
    
            let params = new URLSearchParams({
                date: this.$el.find("#date").val(),
                start_time: this.$el.find("#start_time").val(),
                end_time: this.$el.find("#end_time").val(),
                tables: this.$el.find("#tables_input").val(),
                floors: this.$el.find("#floors").val(),
            });
    
            window.location.href = "/web/login?redirect=/booking/confirm?" + params.toString();
        }
    }

});
