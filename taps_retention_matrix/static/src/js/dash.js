odoo.define('taps_retention_matrix.Dashboard', function(require)){
"use strict";

var AbstractAction = require('web.AbstractAction');
var core = require('web.core');
// var QWeb = core.qweb;

var RetentionDashboard = AbstractAction.extend({
	template: 'Dashboard',

    // init: function(parents, context){
    //     this._super(parents, context); 
    //     this.dashboards_templates = ['DashboardOrders'];
    //     this.today_sale [] = 
    // }

});

core.action_registry.add('custom_dashboard_tag', RetentionDashboard);

return RetentionDashboard;

});