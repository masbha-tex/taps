from odoo import http
from odoo.http import request

class GoogleChartController(http.Controller):
    @http.route('/taps_crm/google_chart', type='json', auth='user')
    def get_google_chart_data(self):
        # Add logic to fetch and prepare data for the Google Chart
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
        return data