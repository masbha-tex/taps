odoo.define('taps_inventory.lot_statusbar', function (require) {
    "use strict";
    var FieldMany2One = require('web.relational_fields').FieldMany2One;

    FieldMany2One.include({
        _render: function () {
            var self = this;
            this._super.apply(this, arguments);

            var records = this.records;
            if (records && records.length) {
                records.forEach(function (record) {
                    var rejected = record.data.rejected;
                    if (rejected) {
                        self.$el.find('option[value="' + record.id + '"]').css('background-color', 'red');
                    }
                });
            }
        },
    });
});
