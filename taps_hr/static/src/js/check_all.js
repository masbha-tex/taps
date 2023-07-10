odoo.define('taps_hr.tree_view', function (require) {
    "use strict";
    
    var ListView = require('web.ListView');
    var ListController = require('web.ListController');
    
    ListView.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            var self = this;
            
            this.$buttons.on('click', '.o_tree_check_all', function () {
                self.$el.find('.o_data_row input[name="selected"]').prop('checked', true);
                self._updateSelections();
            });
            
            this.$buttons.on('click', '.o_tree_uncheck_all', function () {
                self.$el.find('.o_data_row input[name="selected"]').prop('checked', false);
                self._updateSelections();
            });
        },
        
        _updateSelections: function () {
            var selectedIds = [];
            this.$el.find('.o_data_row input[name="selected"]:checked').each(function () {
                var recordId = parseInt($(this).closest('.o_data_row').data('id'), 10);
                if (!isNaN(recordId)) {
                    selectedIds.push(recordId);
                }
            });
            
            this.trigger_up('selection_changed', {
                selection: selectedIds,
            });
        },
    });
});