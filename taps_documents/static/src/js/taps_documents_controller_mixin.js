odoo.define('taps_documents.documents_controller_mixin', function (require) {
    'use strict';

    const DocumentsControllerMixin = require('documents.controllerMixin');
    const original_renderChatter = DocumentsControllerMixin._renderChatter;

    DocumentsControllerMixin._renderChatter = async function () {
        document.addEventListener('DOMContentLoaded', function () {
            if (this._selectedRecordIds.length !== 1) {
                return;
            }

            // Temporarily hide attachment button by setting its style to 'display: none'
            const attachmentsButtons = this.el.querySelectorAll('.o_ChatterTopbar_buttonAttachments');
            attachmentsButtons.forEach(button => {
                button.dataset.originalDisplay = window.getComputedStyle(button).display;
                button.style.display = 'none';
            });

            this._closeChatter();
            const props = this._makeChatterContainerProps();
            this._chatterContainerComponent = new ChatterContainerWrapperComponent(
                this,
                components.ChatterContainer,
                props
            );
            const $chatterContainer = $(qweb.render('documents.ChatterContainer'));
            this.$('.o_content').addClass('o_chatter_open');
            if (this.$('.o_documents_mobile_inspector').length) {
                this.$('.o_documents_mobile_inspector').append($chatterContainer);
            } else {
                this.$('.o_content').append($chatterContainer);
            }
            const target = $chatterContainer[0].querySelector(':scope .o_documents_chatter_placeholder');
            this._chatterContainerComponent.mount(target);

            // Restore the original display style for attachment buttons
            attachmentsButtons.forEach(button => {
                const originalDisplay = button.dataset.originalDisplay;
                if (originalDisplay) {
                    button.style.display = originalDisplay;
                } else {
                    button.style.removeProperty('display');
                }
                delete button.dataset.originalDisplay;
            });
        }.bind(this));
    };

    return DocumentsControllerMixin;
});
