odoo.define('taps_sale.ReportingDashboard', function (require) {
    "use strict";

    // console.log("Hi");

    var AbstractAction = require('web.AbstractAction');
    var core = require('web.core')
    var SampleServer = require('web.SampleServer');
    let dashboardValues;
    var QWeb = core.qweb;
    const { Component, useState,onWillStart } = owl.hooks;
    // SampleServer.mockRegistry.add('sale.order/retrieve_dashboard', () => {
    //     return a= Object.assign({}, dashboardValues);
    // });
    
    
   
    
    

    var ReportingDashboard = AbstractAction.extend({
        template : 'ReportingDashboard',
        
        init: function () {
            var self = this;
            this._super.apply(this, arguments);
            
            self._rpc({
                    model: 'sale.team',
                    method: 'get_team_info',
                    // fields: ['team_name'],
                    // domain: [['sales_type', '=', 'oa']],
                    context: self.context,
                }).then(function (result) {
                    // let l = result.length
                    // self.value = result[0].team_name
                    // console.log(result)
                    // var value_list = []
                    // result.forEach(function(value){
                    //     value_list.push({
                           
                    //         'name': value.name
                    //     });
                    // });
                    self.$el.html(QWeb.render("ReportingDashboard", {result: result}));
                    
                });
            
        
        
        }
        
        

        
    });
    

    core.action_registry.add('action_reporting_dashboard', ReportingDashboard);
    return ReportingDashboard;

});