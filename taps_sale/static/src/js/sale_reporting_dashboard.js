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
            self = this;
            self._rpc({
                    model: 'sale.order',
                    method: 'search_read',
                    fields: ['name'],
                    domain: [['sales_type', '=', 'oa']],
                    context: self.context,
                }).then(function (result) {
              
                    return result;
                    
                });
            
        
        
        }
        
        

        
    });

    core.action_registry.add('action_reporting_dashboard', ReportingDashboard);
    return ReportingDashboard;

});