odoo.define('taps_documents.DocumentsInspector', function (require) {
    'use strict';

    var DocumentsInspector = require('documents.DocumentsInspector');

    DocumentsInspector.include({
        _updateButtons: function () {
            this._super.apply(this, arguments); // Call the parent function

            const binary = this.records.some(record => record.data.type === 'binary');
            if (this._isLocked) {
                this.$('.o_inspector_download').prop('disabled', true);
                this.$('.o_inspector_share').prop('disabled', true);
                this.$('.o_inspector_replace').prop('disabled', true);
                this.$('.o_inspector_delete').prop('disabled', true);
                this.$('.o_inspector_archive').prop('disabled', true);
                this.$('.o_inspector_lock').prop('disabled', true);
                this.$('.o_inspector_split').prop('disabled', true);
                this.$('.o_inspector_table .o_field_widget').prop('disabled', true);
            }
            if (!binary && (this.records.length > 1 || (this.records.length && this.records[0].data.type === 'empty'))) {
                this.$('.o_inspector_download').prop('disabled', true);
            }
        },
        
        // Add any additional custom functions or overrides here
    });

    return DocumentsInspector;
});