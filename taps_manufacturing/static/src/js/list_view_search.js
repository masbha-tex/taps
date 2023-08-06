odoo.define('taps_manufacturing.list_view_search', function (require) {
    "use strict";

    var ListController = require('web.ListController');

    ListController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);

            var self = this;
            var fields = this.renderer.arch.children;

            _.each(fields, function (field) {
                if (field.attrs.custom_search) {
                    var fieldName = field.attrs.name;
                    var $input = $('<input type="text" class="o_input o_search_input"/>');

                    $input.on('keyup', _.debounce(function () {
                        var inputValue = $input.val();
                        var domain = [[fieldName, 'ilike', inputValue]];
                        self.renderer.applySearch(domain);
                    }, 500));

                    $node.find('thead th[data-field="' + fieldName + '"]').append($input);
                }
            });
        },
    });
});
