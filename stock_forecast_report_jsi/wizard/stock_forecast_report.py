import base64
import io
import logging

from odoo.tools.misc import xlsxwriter
from odoo.tools.float_utils import float_round as round
from odoo.tools import format_date
from odoo import fields, models

_logger = logging.getLogger(__name__)


class StockForecastReport(models.TransientModel):
    _name = 'stock.forecast.report'
    _description = 'Stock Forecast Report'

    report_by = fields.Selection([
        ('by_categories', 'By Categories'),
        ('by_products', 'By Products')],
        default='by_categories')
    categ_ids = fields.Many2many('product.category', string='Categories')
    product_ids = fields.Many2many('product.product')
    from_date = fields.Date('From')
    to_date = fields.Date('To', default=fields.Date.context_today)
    file_data = fields.Binary(readonly=True, attachment=False)

    def print_date_wise_stock_register(self):
        Move = self.env['stock.move']
        Product = self.env['product.product']
        start_time = fields.datetime.now()
        from_date = self.from_date
        to_date = self.to_date
        if not (self.product_ids or self.categ_ids):
            products = Product.search([('type', '=', 'product')])
        elif self.report_by == 'by_products':
            products = self.product_ids
        else:
            products = Product.search([('categ_id', 'in', self.categ_ids.ids)])

        # Date wise opening quantity
        product_quantities = products._compute_quantities_dict(False, False, False, from_date, to_date)

        # Received data
        in_moves = Move.read_group([
                ('date', '>=', from_date),
                ('date', '<', to_date),
                ('product_id', 'in', products.ids),
                ('state', '=', 'done'),
                ('picking_code', '=', 'incoming'),
                ('location_dest_id.usage', '=', 'internal')
            ],
            ['product_uom_qty', 'price_unit'],
            ['product_id']
        )
        in_move_dict = dict((item['product_id'][0], (item['product_uom_qty'], item['price_unit'])) for item in in_moves)

        # Issued data
        out_moves = Move.read_group([
                ('date', '>=', from_date),
                ('date', '<', to_date),
                ('product_id', 'in', products.ids),
                ('state', '=', 'done'),
                ('picking_code', '=', 'outgoing')
            ],
            ['product_uom_qty', 'price_unit'],
            ['product_id']
        )
        out_move_dict = dict((item['product_id'][0], (item['product_uom_qty'], item['price_unit'])) for item in out_moves)
        report_data = []

        for categ in products.categ_id:
            report_data.append([categ.display_name])
            categ_products = products.filtered(lambda x: x.categ_id == categ)
            for product in categ_products:
                received_qty = received_price_unit = issued_qty = issued_value = 0
                product_id = product.id

                # Prepare Opening Data
                opening_qty = product_quantities[product_id]['qty_available']
                opening_value = round(opening_qty * product.standard_price, precision_rounding=4)

                # Prepare Received data
                if in_move_dict.get(product_id):
                    received_qty = in_move_dict[product_id][0]
                    received_price_unit = in_move_dict[product_id][1]
                received_value = round(received_qty * received_price_unit, precision_rounding=4)

                # prepare Issued Data
                if out_move_dict.get(product_id):
                    issued_qty = out_move_dict[product_id][0]
                    issued_value = (issued_qty * out_move_dict[product_id][1])

                # Prepare Closing Quantity
                closing_qty = opening_qty + received_qty - issued_qty
                closing_value = opening_value + received_value - issued_value

                product_data = [
                    product.name,
                    opening_qty,
                    opening_value,
                    received_qty,
                    received_value,
                    issued_qty,
                    issued_value,
                    closing_qty,
                    closing_value,
                ]
                report_data.append(product_data)

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet()

        report_title_style = workbook.add_format({'align': 'center', 'bold': True, 'font_size': 16, 'bg_color': '#C8EAAB'})
        worksheet.merge_range('C2:F2', 'Datewise Stock Register', report_title_style)

        report_small_title_style = workbook.add_format({'bold': True, 'font_size': 14})
        worksheet.write(3, 3, ('From %s to %s' % (format_date(self.env, from_date), format_date(self.env, to_date))), report_small_title_style)

        column_product_style = workbook.add_format({'bold': True, 'bg_color': '#EEED8A', 'font_size': 12})
        column_received_style = workbook.add_format({'bold': True, 'bg_color': '#A2D374', 'font_size': 12})
        column_issued_style = workbook.add_format({'bold': True, 'bg_color': '#F8715F', 'font_size': 12})
        row_categ_style = workbook.add_format({'bold': True, 'bg_color': '#6B8DE3'})

        # set the width od the column
        worksheet.set_column(0, 8, 20)

        worksheet.write(6, 0, 'Product', column_product_style)
        worksheet.write(6, 1, 'Opening Quantity', column_product_style)
        worksheet.write(6, 2, 'Opening Value', column_product_style)
        worksheet.write(6, 3, 'Received Quantity', column_received_style)
        worksheet.write(6, 4, 'Received Value', column_received_style)
        worksheet.write(6, 5, 'Issued Quantity', column_issued_style)
        worksheet.write(6, 6, 'Issued Value', column_issued_style)
        worksheet.write(6, 7, 'Closing Quantity', column_product_style)
        worksheet.write(6, 8, 'Closing Value', column_product_style)
        col = 0
        row=7

        for line in report_data:
            col=0
            if len(line) == 1:
                # worksheet.write(row, col, line[0], row_categ_style)
                worksheet.merge_range('A%s:I%s' % (row+1, row+1), line[0], row_categ_style)

            else:
                for l in line:
                    worksheet.write(row, col, l)
                    col+=1
            row+=1
        workbook.close()
        xlsx_data = output.getvalue()

        self.file_data = base64.encodebytes(xlsx_data)
        end_time = fields.datetime.now()
        _logger.info("\n\nTOTAL PRINTING TIME IS : %s \n" % (end_time - start_time))
        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/?model={}&id={}&field=file_data&filename={}&download=true'.format(self._name, self.id, 'StockRegisterReport'),
            'target': 'self',
        }
