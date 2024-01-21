from odoo import http
from odoo.http import request
from odoo.addons.web.controllers.main import ReportController

class CustomChartController(http.Controller):

    @http.route('/taps_crm/get_chart_data', type='json', auth='user')
    def get_chart_data(self, **kw):
        # Fetch data from Odoo models
        labels = [1,2,3]  # Your label data
        values = [10,20,30]  # Your value data
        return {'labels': labels, 'values': values}

    @http.route('/taps_crm/get_chart_data_1', type='json', auth='user')
    def get_chart_data_1(self, **kw):
        # Fetch data from Odoo models
        labels = [1,2,3]  # Your label data
        values = [10,20,30]  # Your value data
        return {'labels': labels, 'values': values}
