odoo.define('taps_lms.greeting_message', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
var time = require('web.time');

var _t = core._t;


var GreetingMessage = AbstractAction.extend({
    contentTemplate: 'LMSAttendanceGreetingMessage',

    // events: {
    //     "click .o_lms_attendance_button_dismiss": function() { this.do_action(this.next_action, {clear_breadcrumbs: true}); },
        
    // },
    events: {
        "click .o_lms_attendance_button_dismiss": function() {
            var self = this;
            this.do_action({
                type: 'ir.actions.act_window',
                res_model: 'lms.session', // Replace with the actual model name of the main menu view
                view_mode: 'form',
                views: [[false, 'form']],
                res_id: self.active_id,
                target: 'current',
                clear_breadcrumbs: true,
            });
        },
    },
    init: function (parent, action) {
        var self = this;
        this._super.apply(this, arguments);
        this.activeBarcode = true;
        this.active_id = action.active_id;
    
        // If no correct action given (due to an erroneous back or refresh from the browser), we set the dismiss button to return
        // to the (likely) appropriate menu, according to the user access rights
        if (!action.attendance) {
            this.activeBarcode = false;
            this.getSession().user_has_group('hr_attendance.group_hr_attendance_user').then(function (has_group) {
                if (has_group) {
                    self.next_action = 'taps_lms.action_barcode_scanner';
                } else {
                    self.next_action = 'taps_lms.action_barcode_scanner';
                }
            });
            return;
        }
    
        this.next_action = action.next_action || 'taps_lms.action_barcode_scanner';
        // No listening to barcode scans if we aren't coming from the kiosk mode (and thus not going back to it with next_action)
        if (this.next_action != 'taps_lms.action_barcode_scanner' && this.next_action.tag != 'taps_lms_barcode_scanner') {
            this.activeBarcode = false;
        }
    
        // Check if the 'attendance' property is defined before accessing it
        // if (action.attendance) {
        // this.attendance = action.attendance;

        // We receive the check in/out times in UTC
        // This widget only deals with display, which should be in the browser's TimeZone
        // this.attendance.attendance_date = this.attendance.attendance_date && moment.utc(this.attendance.attendance_date).local();
        this.previous_attendance_change_date = action.previous_attendance_change_date && moment.utc(action.previous_attendance_change_date).local();

        // Check in/out times displayed in the greeting message template.
        // this.format_time = time.getLangTimeFormat();
        // this.attendance.check_in_time = this.attendance.attendance_date && this.attendance.attendance_date.format(this.format_time);
        // this.attendance.check_out_time = this.attendance.attendance_date && this.attendance.attendance_date.format(this.format_time);
    
            
        // }
        this.format_time = time.getLangTimeFormat();
        if (action.hours_today) {
                var duration = moment.duration(action.hours_today, "hours");
                this.hours_today = duration.hours() + ' hours, ' + duration.minutes() + ' minutes';
            }
        if (action.att_date) {
                this.att_date = action.att_date && moment.utc(action.att_date).local();
                this.att_date_time = this.att_date && this.att_date.format(this.format_time);
            
            }
        
        this.employee_id = action.employee_id;
        this.employee_name = action.employee_name;
        this.attendanceBarcode = action.barcode;
    },

    start: function() {
        if (this.att_date) {
            // this.att_date ? this.farewell_message() : this.welcome_message();
            
            this.welcome_message();
        }
        // this.farewell_message();
        if (this.activeBarcode) {
            core.bus.on('barcode_scanned', this, this._onBarcodeScanned);
        }
        return this._super.apply(this, arguments);
    },

    welcome_message: function() {
        var self = this;
        var now = this.att_date.clone();
        // this.return_to_main_menu = setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);
        this.return_to_main_menu = setTimeout(function() {
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'lms.session',
                view_mode: 'form',
                views: [[false, 'form']],
                res_id: self.active_id,
                target: 'current',
                clear_breadcrumbs: true,
            });
        }, 5000);
                                           

        if (now.hours() < 5) {
            this.$('.o_lms_attendance_message_message').append(_t("Good night"));
        } else if (now.hours() < 12) {
            if (now.hours() < 8 && Math.random() < 0.3) {
                if (Math.random() < 0.75) {
                    this.$('.o_lms_attendance_message_message').append(_t("The early bird catches the worm"));
                } else {
                    this.$('.o_lms_attendance_message_message').append(_t("First come, first served"));
                }
            } else {
                this.$('.o_lms_attendance_message_message').append(_t("Good morning"));
            }
        } else if (now.hours() < 17){
            this.$('.o_lms_attendance_message_message').append(_t("Good afternoon"));
        } else if (now.hours() < 23){
            this.$('.o_lms_attendance_message_message').append(_t("Good evening"));
        } else {
            this.$('.o_lms_attendance_message_message').append(_t("Good night"));
        }
        if(this.previous_attendance_change_date){
            var last_check_out_date = this.previous_attendance_change_date.clone();
            if(now - last_check_out_date > 24*7*60*60*1000){
                this.$('.o_lms_attendance_random_message').html(_t("Glad to have you back, it's been a while!"));
            } else {
                if(Math.random() < 0.02){
                    this.$('.o_lms_attendance_random_message').html(_t("If a job is worth doing, it is worth doing well!"));
                }
            }
        }
               
    },

    farewell_message: function() {
        var self = this;
        var now = this.att_date.clone();
        this.return_to_main_menu = setTimeout(function() {
            self.do_action({
                type: 'ir.actions.act_window',
                res_model: 'lms.session',
                view_mode: 'form',
                views: [[false, 'form']],
                res_id: self.active_id,
                target: 'current',
                clear_breadcrumbs: true,
            });
        }, 5000);
        if(this.previous_attendance_change_date){
            var last_check_in_date = this.previous_attendance_change_date.clone();
            if(now - last_check_in_date > 1000*60*60*12){
                this.$('.o_lms_attendance_warning_message').show().append(_t("<b>Warning! Last check in was over 12 hours ago.</b><br/>If this isn't right, please contact Human Resource staff"));
                clearTimeout(this.return_to_main_menu);
                this.activeBarcode = false;
            } else if(now - last_check_in_date > 1000*60*60*8){
                this.$('.o_lms_attendance_random_message').html(_t("Another good day's work! See you soon!"));
            }
        }

        if (now.hours() < 12) {
            this.$('.o_lms_attendance_message_message').append(_t("Have a good day!"));
        } 
        else if (now.hours() < 14) {
            this.$('.o_lms_attendance_message_message').append(_t("Have a nice lunch!"));
            if (Math.random() < 0.05) {
                this.$('.o_lms_attendance_random_message').html(_t("Eat breakfast as a king, lunch as a merchant and supper as a beggar"));
            } else if (Math.random() < 0.06) {
                this.$('.o_lms_attendance_random_message').html(_t("An apple a day keeps the doctor away"));
            }
        } 
        else if (now.hours() < 17) {
            this.$('.o_lms_attendance_message_message').append(_t("Have a good afternoon"));
        } else {
            if (now.hours() < 18 && Math.random() < 0.2) {
                this.$('.o_lms_attendance_message_message').append(_t("Early to bed and early to rise, makes a man healthy, wealthy and wise"));
            } else {
                this.$('.o_lms_attendance_message_message').append(_t("Have a good evening"));
            }
        }
    },

    _onBarcodeScanned: function(barcode) {
        var self = this;
        // self.session = Session;
        if (this.attendanceBarcode !== barcode){
            if (this.return_to_main_menu) {  // in case of multiple scans in the greeting message view, delete the timer, a new one will be created.
                clearTimeout(this.return_to_main_menu);
            }
            core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
            this._rpc({
                    model: 'lms.session',
                    method: 'attendance_scan',
                    args: [barcode, self.active_id,],
                    // context: {'default_session_id': this.session.user_context.default_session_id}, // Pass the current record ID
                })
                .then(function (result) {
                    if (result.action) {
                        self.do_action(result.action);
                    } else if (result.warning) {
                        self.do_warn(result.warning);
                        setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);
                    }
                }, function () {
                    setTimeout( function() { self.do_action(self.next_action, {clear_breadcrumbs: true}); }, 5000);
                });
        }
    },

    destroy: function () {
        core.bus.off('barcode_scanned', this, this._onBarcodeScanned);
        clearTimeout(this.return_to_main_menu);
        this._super.apply(this, arguments);
    },
});

core.action_registry.add('taps_lms_greeting_message', GreetingMessage);

return GreetingMessage;

});
