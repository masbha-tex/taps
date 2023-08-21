odoo.define('taps_manufacturing.FieldChar', function (require) {
    "use strict";
    var rpc = require('web.rpc');
    var fieldRegistry = require('web.field_registry');
    var FieldChar = require('web.basic_fields').FieldChar;

    var LotCodeEnterField = FieldChar.extend({
       _onKeydown: function (ev) {
           this._super.apply(this, arguments);
           if (ev.which === $.ui.keyCode.ENTER) {
             var self = this;
                var value = this.$input.val();
                rpc.query({
                    model: 'mrp.output',
                    method: 'onevent_lot',
                    args: [value]
                }).then(function (result) {
                    
                });
            }
        },
    });

    fieldRegistry.add('lot_code_enter', LotCodeEnterField);

    return LotCodeEnterField;
});




// odoo.define('taps_manufacturing.FieldChar', function (require) {
//     "use strict";

//     var core = require('web.core');
//     var FormController = require('web.FormController');
//     var FormView = require('web.FormView');

//     FormController.include({
//         _onKeydown: function (ev) {
//             if (ev.which === $.ui.keyCode.ENTER && $(ev.target).is('input[type="text"]')) {
//                 ev.preventDefault();
//                 var $currentField = $(ev.target);
//                 var $nextField = $currentField.closest('.o_field_widget').next('.o_field_widget');
//                 while ($nextField.length > 0 && !$nextField.find('input[type="text"]').length) {
//                     $nextField = $nextField.next('.o_field_widget');
//                 }
//                 if ($nextField.length > 0) {
//                     $nextField.find('input[type="text"]').focus();
//                 }
//             } else {
//                 this._super.apply(this, arguments);
//             }
//         },
//     });

//     FormView.include({
//         config: _.extend({}, FormView.prototype.config, {
//             Controller: FormController,
//         }),
//     });
// });



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