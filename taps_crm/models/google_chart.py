from odoo import http
from odoo.http import request

class GoogleChartController(http.Controller):
    @http.route('/taps_crm/get_google_chart_action', type='json', auth='user')
    def get_google_chart_action(self):
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

