odoo.define('taps_sale.ReportingDashboard', function (require) {
    "use strict";

    console.log("loaded")

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core')
    var SampleServer = require('web.SampleServer');
    let dashboardValues;
    
    SampleServer.mockRegistry.add('sale.order/retrieve_dashboard', () => {
        return a= Object.assign({}, dashboardValues);
    });
    
    

    
    

    var ReportingDashboard = AbstractAction.extend({
        template : 'ReportingDashboard',
        
        init: function () {
            this._super.apply(this, arguments);
            this.dashboardValues = {};
            
            
        
        },
        
        
        _loadDashboard: function (super_def) {
        var self = this;
        var dashboard_def = this._rpc({
            model: 'sale.order',
            method: 'retrieve_dashboard',
            
        });
        return Promise.all([super_def, dashboard_def]).then(function(results) {
            var id = results[0];
            dashboardValues = results[1];
            self.dashboardValues[id] = dashboardValues;
            return id;
        });
        }
        
        
        // _render: function () {
        // var self = this;
        // return this._super.apply(this, arguments).then(function () {
        //     var values = self.state.dashboardValues;
        //     var sale_dashboard = QWeb.render('ReportingDashboard', {
        //         values: values,
        //     });
            
        //     // self.$el.parent().find(".o_sale_dashboard").remove();
        //     self.$el.before(sale_dashboard);
        // });
        // },
    //     _renderView: function () {
    //     var self = this;
    //     return this._super.apply(this, arguments).then(function () {
    //         var values = self.state.dashboardValues;
    //         var sale_dashboard = QWeb.render('ReportingDashboard', {
    //             values: values,
    //         });
    //         self.$el.prepend(sale_dashboard);
    //     });
    // },

        
    });

    core.action_registry.add('action_reporting_dashboard', ReportingDashboard);
    return ReportingDashboard;

});