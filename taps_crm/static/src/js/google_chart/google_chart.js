odoo.define('taps_crm.google_chart_widget', function (require) {
    'use strict';

    var Widget = require('web.Widget');

    var GoogleChartWidget = Widget.extend({
        start: function () {
            google.charts.load('current', {'packages':['corechart']});
            google.charts.setOnLoadCallback(this.drawChart.bind(this));
            return this._super.apply(this, arguments);
        },

        drawChart: function () {
            var data = new google.visualization.arrayToDataTable(this.widget_data.columns);
            var options = this.widget_data.options;
            var chart = new google.visualization[this.widget_data.type](this.el);
            chart.draw(data, options);
        },
    });

    return GoogleChartWidget;
});
