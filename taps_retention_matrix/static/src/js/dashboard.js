odoo.define('taps_retention_matrix.dashboard', function (require) {
    "use strict";

    var core = require('web.core');
    var AbstractAction = require('web.AbstractAction');

    var _t = core._t;

    var MyDashboard = AbstractAction.extend({
        template: 'my_module.RetentionDashboard',
        events: {
            'click .company_id': '_onCompanyClick',
            'click .department_id': '_onDepartmentClick',
        },

        _onCompanyClick: function (ev) {
            var companyId = ev.currentTarget.dataset.id;
            this._retrieveDashboard(companyId);
        },

        _onDepartmentClick: function (ev) {
            var departmentId = ev.currentTarget.dataset.id;
            this._retrieveDashboard(departmentId);
        },

        _retrieveDashboard: function (id) {
            this._rpc({
                model: 'retention.matrix',
                method: 'retrieve_dashboard',
                args: [id],
            }).then(function (result) {
                // Handle the result and update the view accordingly
            });
        },
    });

    core.action_registry.add('my_module.dashboard', MyDashboard);

    return MyDashboard;
});
