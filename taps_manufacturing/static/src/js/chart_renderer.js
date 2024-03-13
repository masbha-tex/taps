
odoo.define('taps_manufacturing.chart_renderer', function (require) {
    "use strict";

    var core = require('web.core');
    var Widget = require('web.Widget');
    var ChartRenderer = require('taps_manufacturing.ChartRenderer');

    var ChartRendererWidget = Widget.extend({
        start: function () {
            this.chartRenderer = new ChartRenderer(this, {});
            this.chartRenderer.appendTo(this.$el);
            return this._super();
        },
    });

    core.action_registry.add('chart_renderer_widget', ChartRendererWidget);

    return ChartRendererWidget;
});
