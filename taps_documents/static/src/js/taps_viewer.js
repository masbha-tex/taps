odoo.define('taps_documents.custom_viewer', function (require) {
    'use strict';
    var pdfjsWebApp = require('web.pdf');

    pdfjsWebApp.PDFViewerApplication.prototype.webViewerLoad = function () {
        // Call the parent webViewerLoad function
        this._super.apply(this, arguments);

        // Your custom code starts here
        console.log('Custom webViewerLoad function executed');

        // Add your custom logic here...

        // Your custom code ends here
    };
});
