odoo.define('taps_crm.google_chart_action', function(require) {
    'use strict';

    // var AbstractAction = require('web.AbstractAction');
    // var core = require('web.core');
    // var QWeb = core.qweb;
    var AbstractAction = require('web.AbstractAction');
    var ajax = require('web.ajax');
    var core = require('web.core')
    var SampleServer = require('web.SampleServer');
    // let dashboardValues;
    var QWeb = core.qweb;
    const {
        Component,
        useState,
        onWillStart
    } = owl.hooks;
    var GoogleChartAction = AbstractAction.extend({
        template: 'taps_crm_google_chart_template',
        start: function() {
            var self = this;
            ajax.jsonRpc("/taps_crm/get_google_chart_action", 'call', {})
                .then(function(data) {
                    // Use Chart.js to render the chart
                    // alert(data.labels)
                    google.charts.load('current', {
                        'packages': ['bar']
                    });
                    google.charts.setOnLoadCallback(drawChart_1(data));

                    function drawChart_1(data) {
                        var a =data.columns
                        // alert(a)
                        var data = google.visualization.arrayToDataTable([['Year', 'Sales', 'Expenses'],
                            ['2014', 1000, 400],
                            ['2015', 1170, 460],
                            ['2016', 660, 1120],
                            ['2017', 1030, 540],
                        ]);
                        var options = {
                            chart: {
                                title: 'SALES VS EXPENSE',
                                subtitle: 'Sales, Expenses, and Profit: 2014-2017',
                            },
                            bars: 'horizontal',
                            // height: 350,
                            // width:300
                            
                            
                        };
                        
                        
                        
                        var chart = new google.charts.Bar(document.getElementById('chart_div'));
                        
                        chart.draw(data, google.charts.Bar.convertOptions(options));
                    }
                });
            
            ajax.jsonRpc("/taps_crm/get_google_chart_action_1", 'call', {})
                .then(function(data) {
                    // Use Chart.js to render the chart
                    google.charts.load('current', {'packages':['table']});
                    google.charts.setOnLoadCallback(drawChart_2);

                    function drawChart_2() {

                    var data = new google.visualization.DataTable();
                    data.addColumn('string', 'Team');
                    data.addColumn('number', 'Total Sales');
                    data.addColumn('number', 'Target');
                    data.addRows([
                      ['Turag',  {v: 10000, f: '$10,000'}, {v: 10000, f: '$10,000'}],
                      ['Sangu',   {v:8000,   f: '$8,000'},  {v: 10000, f: '$10,000'}],
                      ['Overseas', {v: 12500, f: '$12,500'}, {v: 10000, f: '$10,000'}],
                      ['Vietnam',   {v: 7000,  f: '$7,000'},  {v: 10000, f: '$10,000'}],
                      ['Shitalakha',   {v: 7000,  f: '$7,000'},  {v: 10000, f: '$10,000'}],
                      ['Karnaphuli',   {v: 7000,  f: '$7,000'},  {v: 10000, f: '$10,000'}],
                      ['India',   {v: 7000,  f: '$7,000'},  {v: 10000, f: '$10,000'}],
                    ]);
            
                    var table = new google.visualization.Table(document.getElementById('chart_div_1'));

                    table.draw(data, {showRowNumber: true,width: '100%', height: '100%'});
            
                    // chart.draw(data, options);
            
                  }
        });

            return this._super.apply(this, arguments);
        },
    });

    core.action_registry.add('taps_crm_google_chart_action', GoogleChartAction);

    return GoogleChartAction;
});