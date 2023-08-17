odoo.define('taps_manufacturing.FieldChar', function (require) {
    "use strict";

    var rpc = require('web.rpc');
    var fieldRegistry = require('web.field_registry');
    var FieldChar = require('web.basic_fields').FieldChar;

    var LotCodeEnterField = FieldChar.extend({
        // events: _.extend({}, CharField.prototype.events, {
        //     'keyup.input': '_onEnterKey',
        // }),
       _onKeydown: function (ev) {
           this._super.apply(this, arguments);
           if (ev.which === $.ui.keyCode.ENTER) {
             var self = this;
                var value = this.$input.val();
                // alert(self);
                rpc.query({
                    model: 'mrp.output',
                    method: 'onevent_lot',
                    args: [value]
                }).then(function (result) {
                    // Handle the result if needed
                });
            }
        },
    });

    fieldRegistry.add('lot_code_enter', LotCodeEnterField);

    return LotCodeEnterField;
});



// odoo.define('event_handle.FieldChar', function (require) {
// "use strict";

// 	var Model = require('web.Model');
//     var FieldChar = require('web.basic_fields').FieldChar;
//     var registry = require('web.field_registry');
// 	var customemodel = new Model('mrp.output');
    
//     var FieldCharCustom = FieldChar.extend({
//         _onKeydown: function (ev) {
//             if (ev.which === $.ui.keyCode.ENTER) {
//                 alert('sfefe');
//                 customemodel.call('_onevent_lot');
//             }
//             this._super.apply(this, arguments);
//         },
//     });

//     registry.add('char_custom', FieldCharCustom);

// });