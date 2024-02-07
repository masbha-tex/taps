from odoo import http
from odoo.http import request

class GoogleChartController(http.Controller):
    @http.route('/taps_crm/get_google_chart_action', type='json', auth='user')
    def get_google_chart_action(self, **kw):
        labels_and_values = [
            ['Year', 'Sales', 'Expenses'],
            ['2014', 1000, 400],
            ['2015', 1170, 460],
            ['2016', 660, 1120],
            ['2017', 1030, 540]
        ]
        return labels_and_values


    @http.route('/taps_crm/get_google_chart_action_1', type='json', auth='user')
    def get_google_chart_action_1(self):
        data = {
            'columns': [
                ['Task', 'Hours per Day'],
                ['Work', 11],
                ['Eat', 2],
                ['Commute', 2],
                ['Watch TV', 2],
                ['Sleep', 7]
            ],
            'type': 'PieChart',
            'options': {'title': 'My Daily Activities'}
        }
        columns = data.get('columns', [])
        chart_type = data.get('type', 'PieChart')
        options = data.get('options', {})

        return {
            'data': {
                'columns': columns,
                'type': chart_type,
                'options': options,
            },
        }

