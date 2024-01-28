odoo.define('taps_manufacturing.FieldChar', function (require) {
    "use strict";
    var rpc = require('web.rpc');
    var fieldRegistry = require('web.field_registry');
    var FieldChar = require('web.basic_fields').FieldChar;

    var LotCodeEnterField = FieldChar.extend({
       _onKeydown: function (ev) {
           this._super.apply(this, arguments);
           // this.$target_input = $('<input>');
           alert("I am an alert box!");
           if (ev.which === $.ui.keyCode.ENTER) {
             var self = this;
                var value = this.$input.val();
                rpc.query({
                    model: 'label.print',
                    method: 'onevent_lot',
                    args: [value]
                }).then(function (result) {
                    // $manuf_date.find('input, textarea').focus();
                    // this.$target_input.focus();
                    $('.o_datepicker_input').focus();
                    // var currentDatetime = new Date();
                    // var formattedDatetime = currentDatetime.toISOString();
                    // $('#manuf_date').val(formattedDatetime);
                    // this.$('#manuf_date').val(formattedDatetime);
                    // alert(result[1]);
                });
            }
        },
    });

    fieldRegistry.add('lot_code_enter_pack', LotCodeEnterField);

    return LotCodeEnterField;
});



// odoo.define('taps_manufacturing.manufacturing_output', function (require) {
//     "use strict";

//     var FormController = require('web.FormController');

//     FormController.include({
//         _onFieldKeydown: function (ev) {
//             this._super.apply(this, arguments);
//             if (ev.which === 13) {  // Enter key
//                 alert('sfefefe')
//                 this.renderer.state.enter_pressed = true;
//             }
//         },
//     });

// });





// odoo.define('taps_manufacturing.assets_backend', function (require) {
//     "use strict";

//     var FormController = require('web.FormController');

//     FormController.include({
//         on_attach_callback: function () {
//             this._super.apply(this, arguments);
//             var self = this;

//             // Attach keydown event listener to the lot_code field
//             this.$('.o_field_char').on('keydown', function (event) {
//                 if (event.keyCode === 13) {  // Enter key
//                     event.preventDefault();
//                     var inputValue = $(this).val();
//                     self._updateFields(inputValue);
//                     self._simulateTabKey($(this));
//                 }
//             });
//         },

//         _updateFields: function (value) {
//             // Update other fields based on the entered value
//             this.$('.o_field_char[name="oa_id"]').val(value);
//             this.$('.o_field_char[name="item"]').val(value);
//             this.$('.o_field_char[name="shade"]').val(value);
//             this.$('.o_field_char[name="finish"]').val(value);
//             this.$('.o_field_char[name="output_of"]').val(value);
//         },

//         _simulateTabKey: function ($inputField) {
//             var $nextField = $inputField.closest('.o_field_widget').next('.o_field_widget');
//             if ($nextField.length) {
//                 $nextField.find('input, textarea').focus();
//             }
//         },
//     });
// });



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