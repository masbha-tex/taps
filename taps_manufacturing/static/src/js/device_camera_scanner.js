odoo.define('device_camera.barcode_scanner', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');

    var _t = core._t;

    var BarcodeScannerWidget = Widget.extend({
        template: 'barcode_scanner_view',

        events: {
            'click #scan_button': 'scanBarcode',
        },

        init: function (parent) {
            this._super.apply(this, arguments);
            this.barcodeInput = null;
        },

        start: function () {
            this.barcodeInput = this.$('#barcode_input');
            return this._super.apply(this, arguments);
        },

        scanBarcode: function () {
            var self = this;

            Quagga.init({
                inputStream: {
                    name: "Live",
                    type: "LiveStream",
                    target: document.querySelector('#camera_feed'), // Replace with the ID of the element where you want to display the camera feed
                },
                decoder: {
                    readers: ["ean_reader"] // Specify the barcode types you want to scan
                }
            }, function (err) {
                if (err) {
                    console.error(err);
                    return;
                }
                Quagga.start();
            });

            Quagga.onDetected(function (data) {
                self.barcodeInput.val(data.codeResult.code);
                Quagga.stop();
            });
        },
    });

    core.action_registry.add('barcode_scanner_action', BarcodeScannerWidget);

    return BarcodeScannerWidget;
});
