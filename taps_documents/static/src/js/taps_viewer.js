odoo.define('taps_documents.custom_viewer', function (require) {
    'use strict';
    // console.log("hi,");
    // var PDFViewerApplication = require('web.static.lib.pdfjs.web.viewer');
    // var pdfjsWebApp = require('web.static.lib.pdfjs.web.viewer');
    
    // PDFViewerApplication.prototype.webViewerLoad = function () {
    //     // Call the parent webViewerLoad function
    //     this._super.apply(this, arguments);

    //     // Your custom code starts here
    //     console.log("hi, I am here");

    //     // For example, let's add a custom event after the existing 'webviewerloaded' event
    //     var customEvent = document.createEvent('CustomEvent');
    //     customEvent.initCustomEvent('customwebviewerloaded', true, true, {});
    //     document.dispatchEvent(customEvent);

    //     // You can add more custom code here...

    //     // Your custom code ends here
    // };

    var webViewerLoad = require('web.viewer');

    webViewerLoad.include({
        start: function () {
            // Call the parent start method
            this._super.apply(this, arguments);

            // Your custom code here
            console.log("Custom start method");

            // You can add more custom code here...

            return this;
        },
    });
});