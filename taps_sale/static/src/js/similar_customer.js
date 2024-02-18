odoo.define('taps_sale.get_similar_customers_popup', function (require) {
    "use strict";

    var core = require('web.core');
    var Dialog = require('web.Dialog');
    var rpc = require('web.rpc');

    var _t = core._t;

    var openSimilarCustomersPopup = function (customerName, context) {
        rpc.query({
            model: 'provisional.template',
            method: 'get_similar_customers',
            args: [customerName],
            context: context
        }).then(function (result) {
            var $ul = $('<ul>');
            result.forEach(function (name) {
                $ul.append($('<li>').text(name));
            });
            new Dialog(null, {
                size: 'medium',
                $content: $ul,
                buttons: [{
                    text: _t('Close'),
                    close: true,
                }]
            }).open();
        });
    };

    return openSimilarCustomersPopup;
});