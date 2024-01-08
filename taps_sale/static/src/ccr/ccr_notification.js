odoo.define('taps_sale.notification', function (require) {
    "use strict";

    var bus = require('bus.bus');
    var MockServer = require('web.MockServer');  // Add the 'web.MockServer' module
    var core = require('web.core');

    var _t = core._t;

    // Listen for button click
    $(document).ready(function () {
        $(document).on('click', '#sales_approval', function () {
            // Replace with the actual user ID
            var userId = session.uid;

            // Send notification to the user
            bus.trigger('notebook_notify', 'notify_approval', {
                title: _t('Approval Notification'),
                message: _t('Your request has been approved.'),
                sticky: true,
                user_id: userId,
            });
        });
    });
});
