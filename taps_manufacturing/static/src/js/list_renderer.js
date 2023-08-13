odoo.define('web_listview_sticky_header_column.ListRenderer', function (require) {
    "use strict";

    const ListRenderer = require('web.ListRenderer');

    ListRenderer.include({

        freezeColumnNumber: 0,
        currentScrollLeft: 0,
        currentScrollTop: 0,

        events: _.extend({}, ListRenderer.prototype.events, {
            'click .icon_freeze_column_toggle': '_onToggleFreezeColumns',
        }),

        init: function (parent, state, params) {
            this._super.apply(this, arguments);
            this.isFieldWidget = ['one2many', 'many2many'].includes(parent.formatType);
        },

        _renderView: function () {
            return this._super.apply(this, arguments).then(() => {
                if (this.isInDOM) {
                    this._prepareFreezeHeader();
                }
            });
        },

        _renderHeader: function () {
            const $thead = this._super.apply(this, arguments);
            const $th = $thead.find('th');
            $th.each((index, ele) => {
                $(ele).append($('<i>', {
                    class: 'fa fa-thumb-tack icon_freeze_column_toggle',
                }))
            })
            return $thead;
        },
        
        _disableFreezeColumns: function () {
            const currentActiveIcon = this.el.querySelector('.icon_freeze_column_toggle.active');
            if (currentActiveIcon) {
                currentActiveIcon.classList.remove('active');
            }
            const freezeCells = this.el.querySelectorAll('.freeze');
            freezeCells.forEach(cell => {
                cell.classList.remove('freeze');
                cell.style.left = '';
            })
            this.freezeColumnNumber = 0;
            return currentActiveIcon;
        },

        _getScrollObjectHorizontal: function () {
            this.scrollObjectHorizontalClass = this.withSearchPanel ? 'o_renderer_with_searchpanel' :
                this.isFieldWidget ? 'table-responsive' : 'o_content';
            return document.getElementsByClassName(this.scrollObjectHorizontalClass)[0];
        },

        _getScrollObjectVertical: function (className=null) {
            this.scrollObjectVerticalClass = className || (this.withSearchPanel ? 'o_renderer_with_searchpanel' : 'o_content');
            return document.getElementsByClassName(this.scrollObjectVerticalClass)[0];
        },

        _onResize: function () {
            this._prepareFreezeHeader();
            this._prepareFreezeColumns();
        },

        _onScrollObjectScrollingHorizontal: function () {
            if (this.freezeColumnNumber === 0) {
                return
            }
            if (this.scrollObjectHorizontal.scrollLeft === this.currentScrollLeft) {
                return
            }
            this.currentScrollLeft = this.scrollObjectHorizontal.scrollLeft;
            const left = this.currentScrollLeft + 'px';
            this.freezeHeaderCells.forEach(th => {
                th.style.left = left;
            })
            this.freezeBodyCells.forEach(td => {
                td.style.left = left;
            })
        },

        _onScrollObjectScrollingVertical: function () {
            let top = 0;
            if (!this.isFieldWidget) {
                top = this.scrollObjectVertical.scrollTop;
            } else {
                const elOffsetTop = this.el.offsetTop;
                const scrollTop = this.scrollObjectVertical.scrollTop;
                const headerHeight = document.getElementsByTagName('header')[0].offsetHeight;
                const noSheet = !!document.getElementsByClassName('o_form_nosheet')[0];
                const offsetExtra = noSheet ? -48 : 1;
                top = scrollTop - elOffsetTop - headerHeight - offsetExtra;
            }
            if (top < 0) {
                top = 0;
            }
            if (top === this.currentScrollTop) {
                return
            }
            this.currentScrollTop = top;
            const tableHeight = this.el.querySelector('table').clientHeight;
            const tableHeaderHeight = this.el.querySelector('thead').clientHeight;
            if (top + tableHeaderHeight >= tableHeight) {
                return
            }
            this.thElements.forEach(th => {
                th.style.top = top + 'px';
            })
            if (this.optionalFieldsToggler) {
                this.optionalFieldsToggler.style.top = top + 'px';
            }
        },

        _onScrollSheet: function () {
            const sheet = document.getElementsByClassName('o_form_sheet_bg')[0];
            if (!sheet) {
                return
            }
            sheet.removeEventListener('scroll', this._onScrollSheet.bind(this))
            this._setScrollObjectVertical('o_form_sheet_bg');
            this.scrollObjectVertical.addEventListener('scroll', this._onScrollObjectScrollingVertical.bind(this));
        },

        _onToggleFreezeColumns: function (e) {
            e.stopPropagation();

            const current = this._disableFreezeColumns()
            const icon = e.currentTarget;

            if (icon === current) {
                return
            }

            icon.classList.add('active');

            const thElements = [...this.el.querySelectorAll('th')];
            const columnIndex = thElements.indexOf(icon.parentNode);
            this.freezeColumnNumber = columnIndex + 1;
            this._prepareFreezeColumns();
        },

        _prepareFreezeColumns: function () {
            if (this.freezeColumnNumber === 0) {
                return
            }
            this.scrollObjectHorizontal = this._getScrollObjectHorizontal();
            if (!this.scrollObjectHorizontal) {
                return;
            }
            this.freezeHeaderCells = this.el.querySelectorAll(`thead th:nth-child(-n+${this.freezeColumnNumber})`);
            this.freezeHeaderCells.forEach(th => {
                th.classList.add('freeze');
            })

            this.freezeBodyCells = this.el.querySelectorAll(`tbody tr > *:nth-child(-n+${this.freezeColumnNumber}):not([colspan])`);
            this.freezeBodyCells.forEach(td => {
                td.classList.add('freeze');
            })

            this.scrollObjectHorizontal.addEventListener('scroll', this._onScrollObjectScrollingHorizontal.bind(this));
        },

        _prepareFreezeHeader: function () {
            const table = this.el.querySelector('table');
            if (!table) {
                return
            }
            const thead = table.querySelector('thead');
            if (!thead) {
                return
            }
            this.thElements = thead.querySelectorAll('th');
            if (!this.thElements) {
                return
            }
            this._setScrollObjectVertical();
            if (!this.scrollObjectVertical) {
                return;
            }

            this.optionalFieldsToggler = this.el.getElementsByClassName('o_optional_columns_dropdown_toggle')[0];

            this.scrollObjectVertical.addEventListener('scroll', this._onScrollObjectScrollingVertical.bind(this));

            const sheet = document.getElementsByClassName('o_form_sheet_bg')[0];
            if (!sheet) {
                return;
            }
            sheet.addEventListener('scroll', this._onScrollSheet.bind(this));
        },

        _setScrollObjectVertical: function (className=null) {
            this.scrollObjectVertical = this._getScrollObjectVertical(className);
        },

        on_attach_callback: function () {
            this._super.apply(this, arguments);
            this._prepareFreezeHeader();
        },

    })

});
