odoo.define('kiosk_jobcard.kioskjobcard', function (require) {"use strict";
    var Model = require('web.Model')
    var kiosk_jobcard = new Model('kiosk.jobcard')
    kiosk_jobcard.call('open_attendance')
});