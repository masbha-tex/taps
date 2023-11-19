odoo.define('taps_documents.custom_viewer', function (require) {
    'use strict';

    // Register your module and define dependencies
    var core = require('web.core');

    // Wait for the document to be fully loaded
    $(document).ready(function () {
        // Use Odoo's framework to handle deferred DOM nodes
        var targetNode = document.getElementById('print');
        
        // Check if the target node exists
        if (targetNode) {
            // Hide the button by setting its style to "display: none;"
            targetNode.style.display = 'none';
        }
    });
});
