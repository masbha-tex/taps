odoo.define('taps_sale.confirmation_box', function (require) {
    'use strict';

    var core = require('web.core');
    var Dialog = require('web.Dialog');

    var _t = core._t;

    var ConfirmationBox = Dialog.extend({
        template: 'taps_sale.ConfirmationBox',
        events: _.extend({}, Dialog.prototype.events, {
            'click .o_confirm': '_onClickConfirm',
            'click .o_cancel': '_onClickCancel',
        }),

        init: function (parent, options) {
            options = options || {};
            options.title = options.title || _t('Confirmation');
            options.subtitle = options.subtitle || _t('Are you sure?');
            options.confirm_callback = options.confirm_callback || function () {};
            options.cancel_callback = options.cancel_callback || function () {};

            this._super(parent, options);
        },

        start: function () {
            this.$('.modal').addClass('o_confirmation_modal');
            return this._super.apply(this, arguments);
        },

        _onClickConfirm: function () {
            this.options.confirm_callback();
            this.close();
        },

        _onClickCancel: function () {
            this.options.cancel_callback();
            this.close();
        },
    });

    return ConfirmationBox;
});
