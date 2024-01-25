odoo.define('taps_crm.custom_chart', function (require) {
    'use strict';

    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var SampleServer = require('web.SampleServer');
    // let dashboardValues;
    var QWeb = core.qweb;
    const { Component, useState,onWillStart } = owl.hooks;
    
    var CustomChart = AbstractAction.extend({
        template: 'chart_template',

        start: function () {
            var self = this;

            // Fetch data from Odoo models using the Odoo framework
            ajax.jsonRpc("/taps_crm/get_chart_data", 'call', {})
            .then(function (data) {
                // Use Chart.js to render the chart
                var ctx = self.$('#myChart')[0].getContext('2d');
                alert(data.labels)
                var myChart = new Chart(ctx, {
                    type: 'polarArea',
                    data: {
                        
                        // labels: data.labels,
                        labels: ['Red','Green','Yellow','Grey','Blue'],
                        datasets: [{
                            label: 'Sales Data',
                            // data: data.values,
                            data: [11, 16, 7, 3, 14],
                            // backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            backgroundColor: [
                              'rgb(255, 99, 132)',
                              'rgb(75, 192, 192)',
                              'rgb(255, 205, 86)',
                              'rgb(201, 203, 207)',
                              'rgb(54, 162, 235)'
                            ],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                
            });
            
            ajax.jsonRpc("/taps_crm/get_chart_data_1", 'call', {})
            .then(function (data) {
                // Use Chart.js to render the chart
                var ctx_1 = self.$('#myChart_1')[0].getContext('2d');
                var myChart_1 = new Chart(ctx_1, {
                    type: 'doughnut',
                    data: {
                        // labels: data.labels,
                        labels: ['Red','Green','Yellow','Grey','Blue'],
                        datasets: [{
                            label: 'Sales Data',
                            // data: data.values,
                            data: [11, 16, 7, 3, 14],
                            // backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            backgroundColor: [
                              'rgb(255, 99, 132)',
                              'rgb(75, 192, 192)',
                              'rgb(255, 205, 86)',
                              'rgb(201, 203, 207)',
                              'rgb(54, 162, 235)'
                            ],
                            borderColor: 'rgba(75, 192, 192, 1)',
                            borderWidth: 1
                        }]
                    },
                    options: {
                        scales: {
                            y: {
                                beginAtZero: true
                            }
                        }
                    }
                });
                
            });

            return this._super.apply(this, arguments);
        },
    });
    core.action_registry.add('action_reporting_dashboard', CustomChart);
    // return ReportingDashboard;
    return CustomChart;
});
